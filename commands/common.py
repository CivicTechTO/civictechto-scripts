import click
import csv
import functools
import hashlib
import re


ENVVAR_PREFIX = 'CTTO'

def common_params(func):
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
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def prefix_envvar(str):
    return ENVVAR_PREFIX + '_' + str

def get_md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def echo_config(dict, fields):
    for k, v in dict.items():
        if k in fields:
            click.echo('{}: {}'.format(k, v))

def parse_gdoc_url(url):
    GDOC_URL_RE = re.compile('https://docs.google.com/(?:spreadsheets|document)/d/([\w_-]+)/(?:edit|view)(?:#gid=([0-9]+))?')
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
