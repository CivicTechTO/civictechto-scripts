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
    # TODO: handle multiple channels
    # TODO: resolve channels from name
    channel = res['channel']

    ### Fetch spreadsheet

    spreadsheet_key, worksheet_id = parse_gdoc_url(gsheet)
    CSV_URL_TEMPLATE = 'https://docs.google.com/spreadsheets/d/{key}/export?format=csv&id={key}&gid={id}'
    csv_url = CSV_URL_TEMPLATE.format(key=spreadsheet_key, id=worksheet_id)
    # Fetch and parse shortlink CSV.
    r = requests.get(csv_url)
    if r.status_code != requests.codes.ok:
        raise click.Abort()
    # TODO: Clean up this.
    csv_content = r.content.decode('utf-8')
    csv_content = csv_content.split('\r\n')

    ### Confirm spreadsheet title

    # TODO: Move this into class.
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
              * Slack Channel:           #{channel}
              * Spreadsheet - Worksheet: {name}
              * Spreadsheet URL:         {url}"""
              # TODO: Find and display spreadsheet title
              # Get from the file download name.
        confirmation_details = confirmation_details.format(channel=channel['name'], url=gsheet, name=filename)
        click.echo(textwrap.dedent(confirmation_details))

    if not yes:
        click.confirm('Do you want to continue?', abort=True)

    if noop:
        # TODO: Add no-op.
        raise NotImplementedError

    gspread = CustomGSpread()
    wsheet = gspread.get_worksheet(spreadsheet_key, worksheet_id)
    values = wsheet.get_all_values()
    row_count = len(values)
    headers = values[0]
    col_count = len(headers)
    cell_list = wsheet.range(1, 1, row_count, col_count)

    members = sc.get_user_members(channel['id'])

    insert_count = 0
    for m in members:
        # TODO: Confirm that this is what ends up being displayed in Slack.
        username = m['profile']['display_name_normalized'] if m['profile']['display_name_normalized'] else m['profile']['real_name_normalized']
        data = {}
        data['first_name']     = m['profile'].get('first_name', '')
        data['last_name']      = m['profile'].get('last_name', '')
        data['slack_id']       = m['id']
        data['slack_username'] = username
        data['avatar_url']     = m['profile']['image_192']

        try:
            match = next(c for c in cell_list if c.value == m['id'])
        except StopIteration:
            match = None

        if match:
            # Update existing member row
            is_locked = lambda c: c.value.startswith('lock:')
            SKIP_VALUES = ['pass', 'skip', 'none']
            is_skippable = lambda c: c.value.lower() in SKIP_VALUES

            cells_to_update = []

            row_cells = [c for c in cell_list if c._row == match._row]
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
        else:
            # Create new member row
            row_values = []
            for h in headers:
                row_values.append(data.get(h, ''))
            range = "'{}'!{row}:{row}".format(wsheet.title, row=row_count+1+insert_count)
            params = {'valueInputOption': 'RAW'}
            body = {'values': [row_values]}
            # NOTE: append and insert endpoints in the Google Sheets API seem to have a bug, so using a hack a update for now.
            # See: https://github.com/burnash/gspread/issues/551_
            # TODO: Accomodate when no extra rows in table.
            wsheet.spreadsheet.values_update(range, params, body)
            insert_count += 1

if __name__ == '__main__':
    update_member_roster()
