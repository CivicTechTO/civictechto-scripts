import click
import gspread
import re
import requests
import textwrap
import urllib

from gspread.exceptions import CellNotFound
from oauth2client.service_account import ServiceAccountCredentials

from commands.common import common_params, parse_gdoc_url, InsensitiveDictReader
from commands.utils.slackclient import CustomSlackClient
from commands.utils.gspread import CustomGSpread


CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

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
              help='Name or ID of Slack channel in which to fetch membership.',
              )
@common_params
def update_member_roster(gsheet, channel, slack_token, yes, verbose, debug, noop):
    """Update a spreadsheet of members based on Slack channel membership."""

    sc = CustomSlackClient(slack_token)
    res = sc.api_call('conversations.info', channel=channel)
    channel = res['channel']

    ### Fetch spreadsheet

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

    if not yes:
        confirmation_details = """\
            We are using the following configuration:
              * Slack Channel:           #{channel}
              * Spreadsheet - Worksheet: {name}
              * Spreadsheet URL:         {url}"""
              # TODO: Find and display spreadsheet title
              # Get from the file download name.
        confirmation_details = confirmation_details.format(channel=channel['name'], url=gsheet, name=filename)
        click.echo(textwrap.dedent(confirmation_details))
        click.confirm('Do you want to continue?', abort=True)

    if noop:
        raise NotImplementedError

    gspread = CustomGSpread()
    wsheet = gspread.get_worksheet(spreadsheet_key, worksheet_id)
    values = wsheet.get_all_values()
    row_count = len(values)
    headers = values[0]
    col_count = len(headers)
    cell_list = wsheet.range(1, 1, row_count, col_count)

    res = sc.api_call('conversations.members', channel=channel['id'])
    member_ids = res['members']
    members = []
    for mid in member_ids:
        res = sc.api_call('users.info', user=mid)
        member = res['user']
        if member['is_bot']:
            continue
        members += [member]

    for m in members:
        try:
            match = wsheet.find(m['id'])
            row_cells = [c for c in cell_list if c._row == match._row]
        except CellNotFound:
            print('TODO: Add row creation logic')
            print(m)
            continue

        if 'profile' in m:
            # TODO: Confirm that this is what ends up being displayed in Slack.
            username = m['profile']['display_name_normalized'] if m['profile']['display_name_normalized'] else m['profile']['real_name_normalized']
            data = {}
            data['first_name']     = m['profile'].get('first_name', '')
            data['last_name']      = m['profile'].get('last_name', '')
            data['slack_id']       = m['id']
            data['slack_username'] = username
            data['avatar_url']     = m['profile']['image_192']

        is_locked = lambda c: c.value.startswith('lock:')
        SKIP_VALUES = ['pass', 'skip', 'none']
        is_skippable = lambda c: c.value.lower() in SKIP_VALUES

        cells_to_update = []
        for i, c in enumerate(row_cells):
            if is_locked(c):
                continue

            if is_skippable(c):
                continue

            header = headers[i]
            if header not in data:
                continue

            # If value is unchanged
            if c.value == data[header]:
                continue

            c.value = data[header]

            cells_to_update.append(c)

        for c in cells_to_update:
            wsheet.update_cell(c._row, c._col, c.value)

if __name__ == '__main__':
    update_member_roster()
