import click
import re
import requests
import textwrap
import urllib

from commands.common import common_params, parse_gdoc_url, InsensitiveDictReader
from commands.utils.slackclient import CustomSlackClient


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

    res = sc.api_call('conversations.members', channel=channel['id'])
    member_ids = res['members']
    for mid in member_ids:
        res = sc.api_call('users.info', user=mid)
        member = res['user']
        if member['is_bot']:
            continue
        if 'profile' in member:
            # TODO: Confirm that this is what ends up being displayed in Slack.
            username = member['profile']['display_name_normalized'] if member['profile']['display_name_normalized'] else member['profile']['real_name_normalized']
            data = {
                'first_name': member['profile'].get('first_name'),
                'last_name': member['profile'].get('last_name'),
                'slack_id': member['id'],
                'slack_username': username,
                'avatar_url': member['profile']['image_72'],
            }
            print(data)

if __name__ == '__main__':
    update_member_roster()
