import click
import csv
import datetime
import meetup.api
import pprint
import pystache
import re
import requests
import textwrap
import time

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

# TODO: Document pipenv support
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--gsheet-url',
              metavar='<url>')
@click.option('--meetup-api-key',
              metavar='<string>')
@click.option('--meetup-group-slug',
              metavar='<string>')
@click.option('--yes', '-y',
              is_flag=True)
@click.option('--debug', '-d',
              is_flag=True,
              default=False)
def gsheet2meetup(meetup_api_key, gsheet_url, meetup_group_slug, yes, debug):
    """Create/update events of a Meetup.com group from a Google Docs spreadsheet."""

    if debug: click.echo('>>> Debug mode: enabled')

    if not yes:
        confirmation_details = """\
            We are using the following configuration:
              * Meetup Group:    {group}
              * Spreadsheet URL: {url}"""
              # TODO: Find and display spreadsheet title
        confirmation_details = confirmation_details.format(group=meetup_group_slug, url=gsheet_url)
        click.echo(textwrap.dedent(confirmation_details))
        click.confirm('Do you want to continue?', abort=True)

    mclient = meetup.api.Client(meetup_api_key)
    response = mclient.GetEvents({
        'group_urlname': meetup_group_slug,
        'status': 'upcoming',
        # re: simple_html_description
        # See: https://www.meetup.com/meetup_api/docs/:urlname/events/#createparams
        'fields': 'venue,simple_html_description,event_hosts',
    })
    meetup_events = response.results

    gsheet_url_re = re.compile('https://docs.google.com/spreadsheets/d/(\w+)/(?:edit|view)(?:#gid=([0-9]+))?')
    matches = gsheet_url_re.match(gsheet_url)

    # Raise error if key not parseable.
    spreadsheet_key = matches.group(1)
    if spreadsheet_key == None:
        raise

    # Assume first worksheet if not specified.
    worksheet_id = matches.group(2)
    if worksheet_id == None:
        worksheet_id = 0

    CSV_URL_TEMPLATE = 'https://docs.google.com/spreadsheets/d/{key}/export?format=csv&id={key}&gid={id}'
    csv_url = CSV_URL_TEMPLATE.format(key=spreadsheet_key, id=worksheet_id)

    # Epoch time used as a cache buster for urls like event description template.
    script_time = int(time.time())

    # Fetch and parse event CSV.
    with requests.Session() as s:
        response = s.get(csv_url)
        content = response.content.decode('utf-8')
        content = content.split('\r\n')
        reader = csv.DictReader(content, delimiter=',')
        reader.fieldnames
        for row in reader:
            # Set date of event start.
            EVENT_START_TIME = '18:30'
            h, m = EVENT_START_TIME.split(':')
            gevent_start = datetime.datetime.strptime(row['date'], '%Y-%m-%d')
            gevent_start = gevent_start + datetime.timedelta(hours=int(h), minutes=int(m))
            # Ignore non-sync'd or past events
            is_truthy = lambda s: s.lower() in ['x', 'y', 'yes', 'true', 't', '1']
            is_past = lambda d: d < datetime.datetime.now()
            if not is_truthy(row['do_update']) or is_past(gevent_start):
                continue
            get_mevent_start = lambda ev: datetime.datetime.fromtimestamp(ev.get('time')/1000)
            [this_event] = [ev for ev in meetup_events if get_mevent_start(ev).date() == gevent_start.date()]

            # TODO: if event doesn't exist, create
            # If event exists, update
            if this_event:
                if debug:
                    click.echo('MATCHED MEETUP EVENT')
                    click.echo(pprint.pformat(this_event))
                    click.echo('SPREADSHEET EVENT DATA')
                    click.echo(pprint.pformat(row))
                # Skip event if not ending in two asterisks "**".
                # We are using this string as a flag for which events to manage.
                is_event_managed = lambda ev: ev['simple_html_description'].endswith('**')
                if not is_event_managed(this_event):
                    skip_event_msg = 'Event on {date} found, but not set to be managed. To manage, add "**" to last line of event description.'
                    click.echo(skip_event_msg.format(date=row['date']))
                    continue

                template_url = "{url}?r={cachebuster}".format(url=row['template_url'], cachebuster=script_time)
                r = requests.get(template_url)
                desc_tmpl = r.text
                # Pass spreadsheet dict into template func, do token replacement via header names.
                desc = pystache.render(desc_tmpl, row)
                # Add "**" to end of description to indicate this event as managed.
                desc = desc + "\n\n**"

                # TODO: set image
                r = mclient.GetPhotoAlbums(group_id=18761715)
                [album] = [a for a in r.results if a['title'] == 'Meetup Group Photo Album']
                r = mclient.GetPhotos(photo_album_id=album['photo_album_id'])
                #click.echo(pprint.pformat(r.results))
                file = open('logo-pl-border-2017.png', 'rb').read()
                r = mclient.CreateGroupPhoto(await=True, group_urlname=meetup_group_slug, main=False, photo=file)
                # TODO unfinished

                r = mclient.GetVenues(group_urlname=meetup_group_slug)
                recent_venues = r.results
                venue = None
                # search prior venues for exact name match
                matched_venues = [v for v in recent_venues if row['venue_name'] == v['name']]
                if matched_venues:
                    venue = matched_venues.pop()
                # search prior venues for partial name match
                if not venue:
                    matched_venues = [v for v in recent_venues if row['venue_name'] in v['name']]
                    if matched_venues:
                        venue = matched_venues.pop()

                # search open public venues for matches
                # TODO: test this and enable
                feature_enabled = False
                if not venue and feature_enabled:
                    r = mclient.GetOpenVenues(group_urlname=meetup_group_slug)
                    nearby_venues = r.results
                    [matched_venue] = [v for v in nearby_venues if v['name'] == row['venue_name']]
                    # TODO: Search partial match?

                # TODO: Fetch venue ID into spreadsheet? Might just be confusing.

                # Set the event hosts from organizer/leadership group members.
                r = mclient.GetProfiles(group_urlname=meetup_group_slug, role='leads')
                lead_profiles = r.results
                host_names = [h.strip().lower() for h in row['hosts'].split(',')]
                # Match names with case-insensitivity.
                host_profiles = [m for m in lead_profiles if m['name'].lower() in host_names]
                # TODO: If 5 slots to used up, choose random organizers (based on criteria of recent attendance?)

                event_data = {
                    'urlname': meetup_group_slug,
                    'id': this_event['id'],
                    'name': row['title_full'],
                    'rsvp_limit': row['rsvp_limit'],
                    'how_to_find_us': row['how_to_find_us'],
                    'description': desc,
                    # Don't RSVP for the user who supplied API token.
                    'self_rsvp': False,
                    'event_hosts': ','.join([str(m['member_id']) for m in host_profiles]),
                }
                response = mclient.EditEvent(**event_data)

if __name__ == '__main__':
    gsheet2meetup(auto_envvar_prefix='CTTO')
