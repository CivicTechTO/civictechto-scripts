import click
import dateutil.parser
import dateutil.tz
import json
import logging
import os
import re
import requests

from datetime import datetime, timedelta
from trello import TrelloClient

from commands.common import common_params
from commands.utils.trello import BreakoutGroup


CARD_IGNORE_LIST = os.getenv('TRELLO_CARD_IGNORE_LIST').split(',')
CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--api-key', '-k',
              required=True,
              envvar='TRELLO_APP_KEY',
              help='Trello API key.',
              )
@click.option('--api-secret', '-s',
              required=True,
              envvar='TRELLO_SECRET',
              help='Trello API token/secret.',
              )
@click.option('--from-list', '-f',
              required=True,
              envvar='TRELLO_LIST_TONIGHT',
              help='Name or ID of Trello list which cards are moved FROM.',
              )
@click.option('--to-list', '-t',
              required=True,
              envvar='TRELLO_LIST_RECENT',
              help='Name or ID of Trello list which cards are moved INTO.',
              )
@click.option('--board', '-b',
              required=True,
              default='EVvNEGK5',
              help='ID of Trello board on which to act.',
              )
@click.option('--stale-days', '-d',
              default=0,
              help='If provided, card not moved unless stale for this many days.',
              )
@common_params
def move_trello_cards(api_key, api_secret, from_list, to_list, board, stale_days, yes, verbose, debug, noop):
    if debug: click.echo('>>> Debug mode: enabled')
    if noop: click.echo('>>> No-op mode: enabled (No operations affecting data will be run)')
    if stale_days:
        raise NotImplementedError

    board_id = board

    client = TrelloClient(
        api_key=api_key,
        api_secret=api_secret,
    )

    board = client.get_board(board_id)
    board_lists = board.get_lists('open')

    def select_list(lists, filter_string):
        field = 'id' if re.match('^[0-9a-f]+$', filter_string) else 'name'
        [board_list] = [l for l in lists if vars(l)[field] == filter_string]
        return board_list

    from_list = select_list(board_lists, from_list)
    to_list = select_list(board_lists, to_list)

    cards = from_list.list_cards()

    template = 'Moving cards from list "{}" to "{}"...'
    click.echo(template.format(from_list.name, to_list.name), err=True)

    for c in cards:
        if c.name in CARD_IGNORE_LIST:
            continue

        date = c.dateLastActivity
        delta = timedelta(days=stale_days)
        now = datetime.now(dateutil.tz.tzutc())
        if debug:
            print(c.name)
            print(date+delta < now)

        if not noop:
            c.change_list(to_list.id)

        if verbose:
            click.echo('Moved card: ' + c.name, err=True)

        if debug:
            click.echo(vars(c), err=True)

    if noop: click.echo('Command exited no-op mode without creating/updating any data.')

if __name__ == '__main__':
    move_trello_cards()
