import click
from commands.upload2gdrive import upload2gdrive
from commands.next_meetup import next_meetup
from commands.announce_booking_status import announce_booking_status

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass

cli.add_command(upload2gdrive)
cli.add_command(next_meetup)
cli.add_command(announce_booking_status)

if __name__ == '__main__':
    cli()
