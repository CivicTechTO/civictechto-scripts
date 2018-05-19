from dotenv import load_dotenv
import json
import logging
import os
import re
import requests

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '.env')
load_dotenv(dotenv_path=filename)

TRELLO_APP_KEY = os.getenv('TRELLO_APP_KEY')
TRELLO_SECRET = os.getenv('TRELLO_SECRET')
LIST_TONIGHT = "Tonight's Pitches"
LIST_ACTIVE = 'Active'
CARD_IGNORE_LIST = os.getenv('CARD_IGNORE_LIST').split(',')

board_url = 'https://trello.com/b/EVvNEGK5/hacknight-projects'
m = re.search('^https://trello.com/b/(?P<board_id>.+?)(?:/.*)?$', board_url)
board_id = m.group('board_id')

data = {
        'key': TRELLO_APP_KEY,
        'token': TRELLO_SECRET,
        'bid': board_id,
        }

url = 'https://api.trello.com/1/boards/{bid}/lists?key={key}&token={token}'.format(**data)
r = requests.get(url)

board_lists = r.json()

[pitch_list] = [l for l in board_lists if l['name'] == LIST_TONIGHT]
[active_list] = [l for l in board_lists if l['name'] == LIST_ACTIVE]

data.update({'lid': pitch_list['id']})
url = 'https://api.trello.com/1/lists/{lid}/cards?key={key}&token={token}'.format(**data)
r = requests.get(url)
pitch_cards= r.json()

template = 'Moving cards from list "{origin_list}" to "{dest_list}"...'
print(template.format(
    origin_list=pitch_list['name'],
    dest_list=active_list['name']))
for c in pitch_cards:
    if c['name'] in CARD_IGNORE_LIST:
        continue

    data.update({'cid': c['id']})
    url = 'https://api.trello.com/1/cards/{cid}?key={key}&token={token}'.format(**data)
    r = requests.put(url, data = {'idList': active_list['id']})
    card = r.json()
    print('Moved card: ' + c['name'])
    logging.debug('Card data: ' + json.dumps(c))
