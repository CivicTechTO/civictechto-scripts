import click
import csv
from html.parser import HTMLParser
import json
import pprint
import re
import requests
import textwrap
import urllib

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])
GSHEET_URL_RE = re.compile('https://docs.google.com/spreadsheets/d/([\w_-]+)/(?:edit|view)(?:#gid=([0-9]+))?')

def parse_gsheet_url(url):
    matches = GSHEET_URL_RE.match(url)

    # Raise error if key not parseable.
    spreadsheet_key = matches.group(1)
    if spreadsheet_key == None:
        raise 'Could not parse key from spreadsheet url'

    # Assume first worksheet if not specified.
    worksheet_id = matches.group(2)
    if worksheet_id == None:
        worksheet_id = 0

    return spreadsheet_key, worksheet_id

def lookup_link(links=[], slashtag=''):
    matched_link = [l for l in links if l['slashtag'] == slashtag]
    if matched_link:
        return matched_link.pop()
    else:
        return None

# See: https://stackoverflow.com/a/36650753/504018
class TitleParser(HTMLParser):
    # Customized: self.found_once ensures we only grab the first tag, as some
    # modern single-page application framewords seem to have multiple.
    # (whatever Meetup.com uses)
    def __init__(self):
        HTMLParser.__init__(self)
        self.match = False
        self.found_already = False
        self.title = ''

    def handle_starttag(self, tag, attributes):
        self.match = True if tag == 'title' else False

    def handle_data(self, data):
        if self.match and not self.found_already:
            self.found_already = True
            self.title = data
            self.match = False

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--gsheet',
              required=True,
              envvar='CTTO_SHORTLINK_GSHEET',
              help='URL to publicly readable Google Spreadsheet, including sheet ID gid',
              metavar='<url>')
@click.option('--rebrandly-api-key',
              required=True,
              help='API key for Rebrandly',
              metavar='<string>')
@click.option('--domain-name', '-d',
              envvar='CTTO_SHORTLINK_DOMAIN',
              help='Shortlink domain on Rebrandly  [required if multiple domains on account]',
              metavar='<example.com>')
@click.option('--yes', '-y',
              help='Skip confirmation prompts',
              is_flag=True)
@click.option('--debug', '-d',
              is_flag=True,
              help='Show full debug output',
              default=False)
@click.option('--noop',
              help='Skip API calls that change/destroy data',
              is_flag=True)
def gsheet2rebrandly(rebrandly_api_key, gsheet, domain_name, yes, debug, noop):
    """Create/update Rebrandly shortlinks from a Google Docs spreadsheet.

    Here are some notes on spreadsheet columns:

        * slashtag: the shortlink component of path.

        * destination_url: where the shortlink points to.

        * If the following columns exist and a --google-creds option is passed, they will be updated:

            * Note: These features are not yet implemented.

            * created: date and time when the link was created and tracking began.

            * clicks: number of click-through since creation.

        * Extra columns will have no effect.

    Sample Spreadsheet:
        https://docs.google.com/spreadsheets/d/12VUXPCpActC77wy6Q8Khyb-iZ_nlNwshO8XswYRj5XE/edit#gid=776462093
    """

    if debug: click.echo('>>> Debug mode: enabled')

    if noop: click.echo('>>> No-op mode: enabled (No operations affecting data will be run)')

    ### Fetch spreadsheet

    spreadsheet_key, worksheet_id = parse_gsheet_url(gsheet)
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

    ### Confirm domain

    r = requests.get('https://api.rebrandly.com/v1/domains',
                     headers={'apikey': rebrandly_api_key})
    if r.status_code != requests.codes.ok:
        raise click.Abort()

    domains = r.json()
    # Ignore service shortlink domains like rebrand.ly itself.
    my_domains = [d for d in domains if d['type'].lower() != 'service']

    # If --domain-name provided, check it.
    if domain_name:
        my_domain = [d for d in domains if d['fullName'] == domain_name]
        if not my_domain:
            click.echo('Provided domain not attached to account. Exitting...')
            raise click.Abort()
        domain = my_domain.pop()

    # If --domain-name not provided, try to determine it.
    else:
        if len(my_domains) > 1:
            click.echo('More than one domain found. Please specify one via --domain option:')
            # TODO: Echo domains.
            raise click.Abort()
        elif not my_domains:
            click.echo('No custom domains attached to account. Exiting...')
            raise click.Abort()
        else:
            # Found the domain, and set name.
            domain = my_domains.pop()
            domain_name = domain['fullName']

    ### Output confirmation to user

    if not yes:
        confirmation_details = """\
            We are using the following configuration:
              * Shortlink Domain:        {domain}
              * Spreadsheet - Worksheet: {name}
              * Spreadsheet URL:         {url}"""
              # TODO: Find and display spreadsheet title
              # Get from the file download name.
        confirmation_details = confirmation_details.format(domain=domain_name, url=gsheet, name=filename)
        click.echo(textwrap.dedent(confirmation_details))
        click.confirm('Do you want to continue?', abort=True)

    r = requests.get('https://api.rebrandly.com/v1/links',
                     data={'domain': {'fullName': domain_name}},
                     headers={'apikey': rebrandly_api_key})
    if r.status_code != requests.codes.ok:
        raise click.Abort()
    links = r.json()

    # Iterate through CSV content and perform actions on data
    reader = csv.DictReader(csv_content, delimiter=',')
    for row in reader:
        # TODO: If destination_url empty, delete link.
        # TODO: Deal with error when editing trashed link.

        # Extract page title after redirects.
        r = requests.get(row['destination_url'], allow_redirects=True)
        parser = TitleParser()
        parser.feed(r.content.decode('utf-8'))
        payload = {
            'slashtag': row['slashtag'],
            # Don't use url with redirect resolution, because permissioned
            # pages (like Google Docs) will redirect to login page.
            'destination': row['destination_url'],
            'title': parser.title,
        }
        if debug: click.echo('>>> resolved as: ' + pprint.pformat(payload))
        link = lookup_link(links, row['slashtag'])
        if link:
            if noop:
                pass
            else:
                r = requests.post('https://api.rebrandly.com/v1/links/'+link['id'],
                                  data=json.dumps(payload),
                                  headers={
                                      'apikey': rebrandly_api_key,
                                      'Content-Type': 'application/json',
                                  })
                if r.status_code != requests.codes.ok:
                    click.echo(pprint.pformat(r.__dict__))
                    raise click.Abort()
                if debug: click.echo('>>> ' + pprint.pformat(r.json()))
            click.echo('Updated shortlink: '+row['slashtag'])
        else:
            if noop:
                pass
            else:
                payload['domain'] = {'fullName': domain_name}
                payload['slashtag'] = row['slashtag']
                r = requests.post('https://api.rebrandly.com/v1/links',
                                  data=json.dumps(payload),
                                  headers={
                                      'apikey': rebrandly_api_key,
                                      'Content-Type': 'application/json',
                                  })
                if r.status_code != requests.codes.ok:
                    click.echo(pprint.pformat(r))
                    raise click.Abort()
                if debug: click.echo('>>> ' + pprint.pformat(r.json()))
            click.echo('Created shortlink: '+row['slashtag'])

    if noop: click.echo('Command exited no-op mode without creating/updating any data.')

if __name__ == '__main__':
    gsheet2rebrandly(auto_envvar_prefix='CTTO')
