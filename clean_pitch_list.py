import click
import json
import logging
import os
import re
import requests

from commands.common import common_params


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
@common_params
def move_trello_cards(api_key, api_secret, from_list, to_list, board, yes, verbose, debug, noop):
    if debug: click.echo('>>> Debug mode: enabled')
    if noop: click.echo('>>> No-op mode: enabled (No operations affecting data will be run)')

    board_id = board

    data = {
            'key': api_key,
            'token': api_secret,
            'bid': board_id,
            }

    url = 'https://api.trello.com/1/boards/{bid}/lists?key={key}&token={token}'.format(**data)
    r = requests.get(url)

    board_lists = r.json()

    def select_list(lists, filter_string):
        field = 'id' if re.match('^[0-9a-f]+$', filter_string) else 'name'
        [board_list] = [l for l in lists if l[field] == filter_string]
        return board_list

    from_list = select_list(board_lists, from_list)
    to_list = select_list(board_lists, to_list)

    data.update({'lid': from_list['id']})
    url = 'https://api.trello.com/1/lists/{lid}/cards?key={key}&token={token}'.format(**data)
    r = requests.get(url)
    cards = r.json()

    template = 'Moving cards from list "{}" to "{}"...'
    click.echo(template.format(from_list['name'], to_list['name']), err=True)

    for c in cards:
        if c['name'] in CARD_IGNORE_LIST:
            continue

        data.update({'cid': c['id']})
        url = 'https://api.trello.com/1/cards/{cid}?key={key}&token={token}'.format(**data)

        if not noop:
            r = requests.put(url, data = {'idList': to_list['id']})

        if verbose:
            click.echo('Moved card: ' + c['name'], err=True)

        if debug:
            click.echo('Card data: ' + json.dumps(c), err=True)

    if noop: click.echo('Command exited no-op mode without creating/updating any data.')

if __name__ == '__main__':
    move_trello_cards()
