import click
import csv
import dateparser
import pystache
import requests

from datetime import datetime

from commands.common import common_params, parse_gdoc_url
from commands.slackclient import CustomSlackClient

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

class InsensitiveDictReader(csv.DictReader):
    # This class overrides the csv.fieldnames property, which converts all fieldnames without leading and trailing spaces and to lower case.

    @property
    def fieldnames(self):
        return [field.strip().lower() for field in csv.DictReader.fieldnames.fget(self)]

    def next(self):
        return InsensitiveDict(csv.DictReader.next(self))

class InsensitiveDict(dict):
    # This class overrides the __getitem__ method to automatically strip() and lower() the input key

    def __getitem__(self, key):
        return dict.__getitem__(self, key.strip().lower())

class Booking(object):
    status = str()

class BookingsProcessor(object):
    EMOJI_BOOKED = ':white_check_mark:'
    EMOJI_NOT_BOOKED = ':heavy_multiplication_x:'
    EMOJI_UNKNOWN = ':question:'
    EMOJI_PROJECT_UPDATE = ':ctto:'

    csv_content = str()
    venue_bookings = []
    speaker_bookings = []
    venue_string = str()
    speaker_string = str()

    def __init__(self, csv_content):
        self.csv_content = csv_content
        self._process_bookings()
        self._generate_emoji()

    def _generate_emoji(self):
        lookup = {
            'booked': self.EMOJI_BOOKED,
            'unbooked': self.EMOJI_NOT_BOOKED,
            'updates': self.EMOJI_PROJECT_UPDATE,
            'unknown': self.EMOJI_UNKNOWN,
        }

        emojis = []
        for b in self.venue_bookings[:10]:
            e = lookup[b.status]
            emojis.append(e)
        self.venue_string = " ".join(emojis)

        emojis = []
        for b in self.speaker_bookings[:10]:
            e = lookup[b.status]
            emojis.append(e)
        self.speaker_string = " ".join(emojis)

    def _process_bookings(self):
        # Iterate through CSV content and perform actions on data
        reader = InsensitiveDictReader(self.csv_content, delimiter=',')
        for row in reader:
            if not row['date']:
                continue

            date = dateparser.parse(row['date'])
            now = datetime.now()
            if date < now:
                continue

            is_emptyish = lambda s: s.lower() in ['tba', 'tbd', '']

            venue_booking = Booking()
            if is_emptyish(row['venue']):
                venue_booking.status = 'unbooked'
            else:
                venue_booking.status = 'booked'
            self.venue_bookings.append(venue_booking)

            speaker_booking = Booking()
            if row['name'] or row['org']:
                speaker_booking.status = 'booked'
                if 'project update' in row['name'].lower():
                    speaker_booking.status = 'updates'
                elif row['name'].startswith('('):
                    speaker_booking.status = 'unknown'
            else:
                speaker_booking.status = 'unbooked'
            self.speaker_bookings.append(speaker_booking)

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--gsheet',
              required=True,
              help='URL to publicly readable Google Spreadsheet.',
              )
@click.option('--slack-token',
              help='API token for any Slack user.',
              envvar='SLACK_API_TOKEN',
              )
@click.option('--channel', '-c',
              required=True,
              help='Name or ID of Slack channel in which to announce.',
              envvar='SLACK_ANNOUNCE_CHANNEL_ORG',
              )
@common_params
def announce_booking_status(gsheet, channel, slack_token, yes, verbose, debug, noop):
    """Notify a slack channel of high-level status for event & speaker booking."""
    if noop:
        raise NotImplementedError

    spreadsheet_key, worksheet_id = parse_gdoc_url(gsheet)
    CSV_URL_TEMPLATE = 'https://docs.google.com/spreadsheets/d/{key}/export?format=csv&id={key}&gid={id}'
    csv_url = CSV_URL_TEMPLATE.format(key=spreadsheet_key, id=worksheet_id)

    # Fetch and parse CSV.
    r = requests.get(csv_url)
    if r.status_code != requests.codes.ok:
        raise click.Abort()
    csv_content = r.content.decode('utf-8')
    csv_content = csv_content.split('\r\n')

    bookings = BookingsProcessor(csv_content)

    tmpl_vars = {
        'venue_statuses': bookings.venue_string,
        'speaker_statuses': bookings.speaker_string,
    }

    thread_template = open('templates/announce_booking_status.txt').read()
    thread_content = pystache.render(thread_template, tmpl_vars)

    if debug or not slack_token:
        print(thread_content)
    else:
        sc = CustomSlackClient(slack_token)
        sc.bot_thread(
            channel=channel,
            thread_content=thread_content,
        )

if __name__ == '__main__':
    announce_booking_status()
