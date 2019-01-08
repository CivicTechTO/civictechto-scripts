import click
import csv
import datetime
import re
import requests

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

# TODO: Document pipenv support
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--gsheet-url',
              default='https://docs.google.com/spreadsheets/d/19B5sk8zq_pYZVe0DMGCKKBP2jYolm6COfJfIq45vwCg/edit#gid=2098195688',
              metavar='<url>')
@click.option('--meetup-api-key',
              metavar='<string>')
@click.option('--meetup-group-slug',
              metavar='<string>')
def gsheet2meetup(meetup_key, gsheet_url, meetup_group_slug):
    """Create/update events of a Meetup.com group from a Google Docs spreadsheet."""

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
            date = datetime.datetime.strptime(row['date'], '%Y-%m-%d')
            date = date + datetime.timedelta(hours=int(h), minutes=int(m))
            # Ignore non-sync'd or past events
            is_past = lambda d: d < datetime.datetime.now()
            if not row['do_sync'] or is_past(date):
                continue
            print(row)

    # parse gsheet event data

    # get meetup.com events

    # foreach gsheet event

        # if exists on meetup.com

            # if flag for management doesn't exist

                # skip

            # update event

        # else

            # select random organizers

            # create new event
    pass

if __name__ == '__main__':
    gsheet2meetup(auto_envvar_prefix='CTTO')
