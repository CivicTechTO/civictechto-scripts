import click
from commands.upload2gdrive import upload2gdrive
from commands.next_meetup import next_meetup

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass

cli.add_command(upload2gdrive)
cli.add_command(next_meetup)

if __name__ == '__main__':
    cli()
