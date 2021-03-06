import click
from collections import defaultdict
import csv
import datetime
import hashlib
import meetup.api
import pprint
import pystache
import random
import re
import requests
import tempfile
import textwrap
import time
import urllib


CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])
GDOC_URL_RE = re.compile('https://docs.google.com/(?:spreadsheets|document)/d/([\w_-]+)/(?:edit|view)(?:#gid=([0-9]+))?')
# Epoch time used as a cache buster for urls like event description template.
SCRIPT_TIME = int(time.time())

def parse_gdoc_url(url):
    matches = GDOC_URL_RE.match(url)

    # Raise error if key not parseable.
    spreadsheet_key = matches.group(1)
    if spreadsheet_key == None:
        raise 'Could not parse key from spreadsheet url'

    # Assume first worksheet if not specified.
    worksheet_id = matches.group(2)
    if worksheet_id == None:
        worksheet_id = 0

    return spreadsheet_key, worksheet_id

def add_cachebuster(url):
    url_data = alturlsplit(url)
    query_data = url_data.query
    # Add to prevent fetching of cached CSV (eg. on GitHub)
    query_data.update({'cachebuster': SCRIPT_TIME})
    url_data = url_data._replace(query=query_data)
    url = alturlunsplit(url_data)
    return url

def alturlsplit(url):
    url_data = urllib.parse.urlsplit(url)
    query_data = urllib.parse.parse_qs(url_data.query)
    url_data = url_data._replace(query=query_data)
    return url_data

def alturlunsplit(url_data):
    query_data = url_data.query
    query_string = '&'.join(['{}={}'.format(k, v) for k, v in query_data.items()])
    url_data = url_data._replace(query=query_string)
    url = urllib.parse.urlunsplit(url_data)
    return url

class dotdefaultdict(defaultdict):
    """dot.notation access to default dictionary attributes"""
    def __init__(self, default_factory):
        super(dotdefaultdict, self).__init__(default_factory)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--gsheet',
              required=True,
              envvar='CTTO_MEETUP_GSHEET',
              help='URL to publicly readable Google Spreadsheet, including sheet ID gid',
              metavar='<url>')
@click.option('--meetup-api-key',
              required=True,
              help='API key for member of leadership team',
              metavar='<string>')
@click.option('--meetup-group-slug',
              required=True,
              help='Meetup group name from URL',
              metavar='<string>')
@click.option('--yes', '-y',
              help='Skip confirmation prompts',
              is_flag=True)
@click.option('--verbose', '-v',
              help='Show output for each action',
              is_flag=True)
@click.option('--debug', '-d',
              is_flag=True,
              help='Show full debug output',
              default=False)
@click.option('--noop',
              help='Skip API calls that change/destroy data',
              is_flag=True)
def gsheet2meetup(meetup_api_key, gsheet, meetup_group_slug, yes, verbose, debug, noop, cautious=False):
    """Create/update events of a Meetup.com group from a Google Docs spreadsheet.

    The following fields are available:

        * do_update: Only rows with a mark here will be updated/created.

        * date: The date of the event to match, format YYYY-MM-DD.

        * title_full: The name of the Meetup event.

        * image_url: Featured event image. Recommended: 600x338 (16:9 ratio)

        * template_url: URL to a plaintext template file. It will be processed
            as a handlebar template, and will pass in all header names as template
            variables for replacement. Create new columns to add new variables.

        * One-for-one fields that pass strings and integers directly as-is:
            how_to_find_us, rsvp_limit, guest_limit, questions

        * venue_name: Looks for exact matches in past venues, then partial
            matches, then exact matches in public open venues. (It will not
            create new venues at the moment.)

        * venue_visibility: Vibility of venue details.
            Options: 'public' or 'members'. Default: members

        * ready_to_announce: Before 7 days in advance of event, marking this
            column with 'x' will send an announcement to group members. (Once per
            event)

        * hosts: Use a comma-separated list of names. For each name, will look
            in the list of group leadership for EXACT matches, then partial.

    If a field is not provided or the column is missing, it will simply be ignored.

    To explicitly unset certain fields, set its value to one of: none, ---, --, -, na, n/a, tbd, tba
    """

    if debug: click.echo('>>> Debug mode: enabled')

    if noop: click.echo('>>> No-op mode: enabled (No operations affecting data will be run)')

    ### Fetch spreadsheet
    if verbose: click.echo('Fetching event information...')

    spreadsheet_key, worksheet_id = parse_gdoc_url(gsheet)
    CSV_URL_TEMPLATE = 'https://docs.google.com/spreadsheets/d/{key}/export?format=csv&id={key}&gid={id}'
    csv_url = CSV_URL_TEMPLATE.format(key=spreadsheet_key, id=worksheet_id)
    # Fetch and parse shortlink CSV.
    r = requests.get(csv_url)
    if r.status_code != requests.codes.ok:
        raise click.Abort()
    csv_content = r.content.decode('utf-8')
    csv_content = csv_content.split('\r\n')

    ### Confirm spreadsheet title

    cd_header = r.headers.get('Content-Disposition')
    # See: https://tools.ietf.org/html/rfc5987#section-3.2.1 (ext-value definition)
    m = re.search("filename\*=(?P<charset>.+)'(?P<language>.*)'(?P<filename>.+)", cd_header)
    filename = m.group('filename')
    filename = urllib.parse.unquote(filename)
    # Remove csv filename suffix.
    filename = filename[:-len('.csv')]

    ### Output confirmation to user

    if verbose or not yes:
        confirmation_details = """\
            We are using the following configuration:
              * Meetup Group:            {group}
              * Spreadsheet - Worksheet: {name}
              * Spreadsheet URL:         {url}"""
              # TODO: Find and display spreadsheet title
              # Get from the file download name.
        confirmation_details = confirmation_details.format(group=meetup_group_slug, url=gsheet, name=filename)
        click.echo(textwrap.dedent(confirmation_details))

    if not yes:
        click.confirm('Do you want to continue?', abort=True)

    mclient = meetup.api.Client(meetup_api_key)
    response = mclient.GetEvents({
        'group_urlname': meetup_group_slug,
        'status': 'upcoming',
        # re: simple_html_description
        # See: https://www.meetup.com/meetup_api/docs/:urlname/events/#createparams
        'fields': 'venue,venue_visibility,simple_html_description,event_hosts',
    })
    meetup_events = response.results

    # Iterate through CSV content and perform actions on data
    reader = csv.DictReader(csv_content, delimiter=',')
    for row in reader:
        # Skip if date not set.
        if not row['date']:
            continue

        # Set date of event start.
        EVENT_START_TIME = '18:30'
        h, m = EVENT_START_TIME.split(':')
        gevent_start = datetime.datetime.strptime(row['date'], '%Y-%m-%d')
        gevent_start = gevent_start + datetime.timedelta(hours=int(h), minutes=int(m))
        # Ignore non-sync'd or past events
        is_truthy = lambda s: s.lower() in ['x', 'y', 'yes', 'true', 't', '1']
        # We're a little generous with the definition of "past", since the
        # script is not timezone-aware. Since it might run in the cloud
        # sometime that is one day offset, we pad a day. We only update
        # "upcoming" events on Meetup.com, so any rows for "past" events (which
        # aren't editable) won't be caught in this.
        is_definitely_past = lambda d: d < datetime.datetime.now()-datetime.timedelta(days=1)

        if is_definitely_past(gevent_start):
            continue

        if not is_truthy(row['do_update']):
            if verbose:
                click.echo('Skipped {} event (re: do_update field)'.format(row['date']))
            continue

        get_mevent_start = lambda ev: datetime.datetime.fromtimestamp(ev.get('time')/1000)
        this_event = [ev for ev in meetup_events if get_mevent_start(ev).date() == gevent_start.date()]
        if this_event:
            this_event = this_event.pop()

        # TODO: if event doesn't exist, create
        if not this_event:
            raise 'Ability to create events not yet implemented, only event update.'

        # If event exists, update
        else:
            # Skip event if not ending in two asterisks "**".
            # We are using this string as a flag for which events to manage.
            is_event_managed = lambda ev: ev['simple_html_description'].endswith('**')
            # TODO: Either add cautious flag or remove this code.
            if cautious and not is_event_managed(this_event):
                skip_event_msg = 'Event on {date} found, but not set to be managed. To manage, add "**" to last line of event description.'
                if verbose:
                    click.echo(skip_event_msg.format(date=row['date']))
                continue

            if debug:
                click.echo('MATCHED MEETUP EVENT')
                click.echo(pprint.pformat(this_event))
                click.echo('SPREADSHEET EVENT DATA')
                click.echo(pprint.pformat(row))

            event_data = {
                'urlname': meetup_group_slug,
                'id': this_event['id'],
                'name': row['title_full'],
                # Don't RSVP for the user who supplied API token.
                'self_rsvp': False,
                # Default to 'members' only
                'venue_visibility': row.get('venue_visibility', 'members')
            }

            # If set to ready, and not yet announced.
            if is_truthy(row['ready_to_announce']) and not this_event['announced']:
                if not yes:
                    click.echo('Meetup: ' + row['title_full'])
                    click.confirm('Are you sure you wish to announce?', abort=True)
                # TODO: Add some check for days prior to event.
                event_data['announce'] = True

            # If a field can be set by a simple string, allow it to be set
            # from self-same spreadsheet column key. Use 'none' to unset, and ignore empty fields.
            API_STR_FIELDS = ['how_to_find_us', 'question']
            API_NUM_FIELDS = ['rsvp_limit', 'guest_limit']
            UNSET_KEYWORDS = ['none', '-', '--', '---', 'n/a', 'na', 'tba', 'tbd']
            for key in row.keys():
                if key in API_STR_FIELDS + API_NUM_FIELDS:
                    if not row[key]:
                        continue
                    if row[key].lower() in UNSET_KEYWORDS:
                        unset_val = '' if key in API_STR_FIELDS else '0'
                        event_data[key] = unset_val
                        continue
                    event_data[key] = row[key]

            # Set event description from template
            if row['template_url']:
                template_url = add_cachebuster(row['template_url'])
                url_data = alturlsplit(template_url)
                if url_data.netloc == 'docs.google.com' and 'document' in url_data.path:
                    gdoc_key, _ = parse_gdoc_url(template_url)
                    TXT_URL_TEMPLATE = 'https://docs.google.com/document/d/{key}/export?format=txt'
                    template_url = TXT_URL_TEMPLATE.format(key=gdoc_key)
                r = requests.get(template_url)
                # Get rid of byte order mark
                # See: https://stackoverflow.com/a/8898439/504018
                desc_tmpl = r.content.decode('utf-8-sig')
                # Linux newlines
                desc_tmpl = desc_tmpl.replace("\r\n", "\n")

                ## DEAL WITH GOOGLE DOCS COMMENTS IN TEMPLATE

                # Strip out comments from end, after last footnote.
                matches = re.finditer('\[a\]', desc_tmpl)
                last_index = list(matches)[-1].start()
                desc_tmpl = desc_tmpl[:last_index]
                # Strip remaining newlines between text and comments.
                desc_tmpl = desc_tmpl.strip()
                # Remove footnote markers from within text.
                desc_tmpl = re.sub(r'\[[a-z]{1,2}\]', '', desc_tmpl)

                # Pass spreadsheet dict into template func, do token replacement via header names.
                desc = pystache.render(desc_tmpl, row)
                # Add "**" to end of description to indicate this event as managed.
                desc = desc + "\n\n**"
                event_data['description'] = desc

            if row['image_url']:
                # TODO: For Google Drive links, convert to direct link.
                # From: https://drive.google.com/open?id=1aVg0AODDtNl97Ntarm53KibO8oMOHVIw (shareable link)
                # To: https://drive.google.com/uc?id=1aVg0AODDtNl97Ntarm53KibO8oMOHVIw (image bytes)
                # Download image from url.
                _, image_path = tempfile.mkstemp()
                r = requests.get(row['image_url'], allow_redirects=True)
                f = open(image_path, 'wb')
                f.write(r.content)
                image_file = open(image_path, 'rb')
                image_checksum = hashlib.md5(image_file.read()).hexdigest()
                image_file.seek(0)

                # Check for and use checksum'd photo if exists.
                r = mclient.GetPhotos(group_urlname=meetup_group_slug)
                dup_photos = [p for p in r.results if image_checksum in p.get('caption', '')]
                if dup_photos:
                    image_obj = dup_photos.pop()
                    photo_id = image_obj['photo_id']
                    if debug:
                        click.echo('>>> Found photo:')
                        click.echo(pprint.pformat(dict(image_obj)))

                # If not, upload the image.
                else:
                    # Get the group default album.
                    r = mclient.GetPhotoAlbums(group_urlname=meetup_group_slug)
                    [album] = [a for a in r.items if a['title'] == 'Meetup Group Photo Album']

                    # Set a caption to tag this photo as managed for this event.
                    caption_tag = 'Featured image for {} event (id: {})'.format(row['date'], image_checksum)

                    # Upload a photo to the default album.
                    if noop:
                        image_obj = dotdefaultdict(lambda: '')
                    else:
                        image_obj = mclient.CreatePhoto(await=True,
                                                         photo_album_id=album['id'],
                                                         caption=caption_tag,
                                                         photo=image_file)
                    photo_id = image_obj.event_photo_id
                    if debug:
                        click.echo('>>> Created photo:')
                        click.echo(pprint.pformat(image_obj.__dict__))

                # TODO: Set to zero to remove ID if none provided. (Or set default.)
                event_data['featured_photo_id'] = photo_id

            if row['venue_name']:
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

                if venue:
                    event_data['venue_id'] = venue['id']
                # TODO: Fetch venue ID into spreadsheet? Might just be confusing.

            if row['hosts']:
                # Set the event hosts from organizer/leadership group members.
                r = mclient.GetProfiles(group_urlname=meetup_group_slug, role='leads')
                lead_profiles = r.results
                host_ids = []
                for name in row['hosts'].split(','):
                    # Match names with case-insensitivity.
                    profile_matches = [p for p in lead_profiles if name.strip().lower() == p['name'].lower()]
                    if not profile_matches:
                        # Partial match if exact not found
                        profile_matches = [p for p in lead_profiles if name.strip().lower() in p['name'].lower()]

                    if profile_matches:
                        match = profile_matches.pop()
                        host_ids.append(str(match['member_id']))

                # Shuffle hosts each time
                random.shuffle(host_ids)
                host_ids = ','.join(host_ids)
                event_data['event_hosts'] = host_ids

            # Ensure fields with errors are never sync'd.
            # For rationale of copy, see: https://stackoverflow.com/a/11941855/504018
            for k, v in dict(event_data).items():
                if '#NAME?' in str(v):
                    click.echo("WARNING {} event: Field '{}' had a error and its update was skipped.".format(row['date'], k))
                    del event_data[k]

            if debug: click.echo(">>> Updating event with current properties:\n" + pprint.pformat(event_data))
            if noop:
                response = dotdefaultdict(lambda: '')
            else:
                response = mclient.EditEvent(**event_data)
                if debug:
                    click.echo('>>> Updated event:')
                    click.echo(pprint.pformat(response.__dict__))

            if verbose:
                click.echo('UPDATED {} event: {}'.format(row['date'], row['title_full']))
                if event_data.get('announce'):
                    click.echo('--- ANNOUNCED')

    if noop: click.echo('Command exited no-op mode without creating/updating any events.')

if __name__ == '__main__':
    gsheet2meetup(auto_envvar_prefix='CTTO')
