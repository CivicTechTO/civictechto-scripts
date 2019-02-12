import click
from commands.upload2gdrive import upload2gdrive

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass

cli.add_command(upload2gdrive)

if __name__ == '__main__':
    cli()
