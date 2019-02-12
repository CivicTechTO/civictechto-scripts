import click
import functools
import hashlib


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
