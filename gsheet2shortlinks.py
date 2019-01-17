import click
import csv
import json
import pprint
import re
import requests
import textwrap

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
    """Create/update Rebrandly shortlinks from a Google Docs spreadsheet."""

    if debug: click.echo('>>> Debug mode: enabled')

    if noop: click.echo('>>> No-op mode: enabled (No operations affecting data will be run)')

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

    if not yes:
        confirmation_details = """\
            We are using the following configuration:
              * Shortlink Domain: {domain}
              * Spreadsheet URL:  {url}"""
              # TODO: Find and display spreadsheet title
              # Get from the file download name.
        confirmation_details = confirmation_details.format(domain=domain_name, url=gsheet)
        click.echo(textwrap.dedent(confirmation_details))
        click.confirm('Do you want to continue?', abort=True)

    spreadsheet_key, worksheet_id = parse_gsheet_url(gsheet)
    CSV_URL_TEMPLATE = 'https://docs.google.com/spreadsheets/d/{key}/export?format=csv&id={key}&gid={id}'
    csv_url = CSV_URL_TEMPLATE.format(key=spreadsheet_key, id=worksheet_id)
    # Fetch and parse shortlink CSV.
    r = requests.get(csv_url)
    content = r.content.decode('utf-8')
    content = content.split('\r\n')
    reader = csv.DictReader(content, delimiter=',')
    for row in reader:
        if debug: click.echo(pprint.pformat(row))

    if noop: click.echo('Command exited no-op mode without creating/updating any data.')

if __name__ == '__main__':
    gsheet2rebrandly(auto_envvar_prefix='CTTO')
