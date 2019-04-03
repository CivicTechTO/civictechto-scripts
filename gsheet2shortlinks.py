import click
import csv
from html.parser import HTMLParser
import json
import pprint
import re
import requests
import textwrap
import urllib

from commands.common import common_params
from commands.utils.rebrandly import Rebrandly, AmbiguousCustomDomainError, NoCustomDomainsExistError

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
@common_params
# TODO: Accomodate --verbose flag.
def gsheet2rebrandly(rebrandly_api_key, gsheet, domain_name, yes, verbose, debug, noop):
    """Create/update Rebrandly shortlinks from a Google Docs spreadsheet.

    Here are some notes on spreadsheet columns:

        * slashtag: the shortlink component of path.

        * destination_url: where the shortlink points to. Leaving blank will delete on next run.

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

    rebrandly = Rebrandly(rebrandly_api_key)
    if domain_name:
        # If --domain-name provided, check it.
        rebrandly.set_domain_by_name(domain_name)
        if not rebrandly.default_domain:
            click.echo('Provided domain not attached to account. Exitting...')
            raise click.Abort()
    else:
        try:
            rebrandly.autodetect_domain()
        except AmbiguousCustomDomainError:
            click.echo('More than one domain found. Please specify one via --domain option:', err=True)
        except NoCustomDomainsExistError:
            click.echo('No custom domains attached to account. Exiting...', err=True)

        domain_name = rebrandly.default_domain['fullName']

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

    # TODO: Move pagination into rebrandly client class.
    all_links = []
    first = True
    last_links = None
    while first or last_links:
        payload = {}
        if last_links:
            payload.update({'last': last_links[-1]['id']})

        r = rebrandly.get('/links',
                         data=payload)
        this_links = r.json()
        all_links += this_links

        last_links = this_links
        first = False

    # Iterate through CSV content and perform actions on data
    reader = csv.DictReader(csv_content, delimiter=',')
    for row in reader:
        link = lookup_link(all_links, row['slashtag'])
        if debug: click.echo(link, err=True)

        # If destination_url empty, delete link.
        if not row['destination_url']:
            if not link:
                click.echo('Non-existent shortlink: {} (already deleted)'.format(row['slashtag']))
                continue

            # NOTE: Not possible to "trash", only to fully delete, as per support chat question.
            r = requests.delete('https://api.rebrandly.com/v1/links/'+link['id'],
                                headers={'apikey': rebrandly_api_key})
            if debug: click.echo(pprint.pformat(r))
            click.echo('Deleted shortlink: '+row['slashtag'])
            continue

        r = requests.get(row['destination_url'], allow_redirects=True)
        if 'text/html' in r.headers['Content-Type']:
            # Extract page title after redirects.
            parser = TitleParser()
            # FIXME: Title parser. Not working.
            title = parser.feed(r.content.decode('utf-8'))
        else:
            title = 'File: '+r.headers['Content-Type']
        payload = {
            'slashtag': row['slashtag'],
            # Don't use url with redirect resolution, because permissioned
            # pages (like Google Docs) will redirect to login page.
            'destination': row['destination_url'],
            'title': title,
        }
        if debug: click.echo('>>> resolved as: ' + pprint.pformat(payload))

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
                if debug: click.echo('>>> ' + pprint.pformat(r.json()))
                if r.status_code != requests.codes.ok:
                    click.echo(pprint.pformat(r.__dict__))
                    raise click.Abort()
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
                if debug: click.echo('>>> ' + pprint.pformat(r.json()))
                if r.status_code != requests.codes.ok:
                    click.echo(pprint.pformat(r))
                    raise click.Abort()
            click.echo('Created shortlink: '+row['slashtag'])

    if noop: click.echo('Command exited no-op mode without creating/updating any data.')

if __name__ == '__main__':
    gsheet2rebrandly(auto_envvar_prefix='CTTO')
