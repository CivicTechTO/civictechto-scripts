from dotenv import load_dotenv
import os
import pystache
import re
from slackclient import SlackClient
import sys
from trello import TrelloClient

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '.env')
load_dotenv(dotenv_path=filename)

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

DEBUG = str2bool(os.getenv('DEBUG', ''))
SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN')
SLACK_ANNOUNCE_CHANNEL = os.getenv('SLACK_ANNOUNCE_CHANNEL')
TRELLO_APP_KEY = os.getenv('TRELLO_APP_KEY')
TRELLO_SECRET = os.getenv('TRELLO_SECRET')
LIST_TONIGHT = "Tonight's Pitches"

client = TrelloClient(
    api_key=TRELLO_APP_KEY,
    api_secret=TRELLO_SECRET,
)

board_url = 'https://trello.com/b/EVvNEGK5/hacknight-projects'
m = re.search('^https://trello.com/b/(?P<board_id>.+?)(?:/.*)?$', board_url)
board_id = m.group('board_id')

board = client.get_board(board_id)
lists = board.get_lists('open')
[pitch_list] = [l for l in lists if l.name == LIST_TONIGHT]
cards = pitch_list.list_cards()

# Assume Trello not used this week
if len(cards) < 3: sys.exit()

template = """
:ctto: :ctto: :ctto: Yay! Thanks so much to everyone who made *this week's pitches*:

{{#projects}}
:small_blue_diamond: {{ name }}
{{/projects}}
"""

if DEBUG:
    print(pystache.render(template.strip(), {'projects': cards}))
else:
    sc = SlackClient(SLACK_API_TOKEN)
    msg = sc.api_call(
            'chat.postMessage',
            channel=SLACK_ANNOUNCE_CHANNEL,
            as_user=False,
            username='civictechto-scripts',
            icon_emoji=':robot_face:',
            text=pystache.render(template.strip(), {'projects': cards})
            )
    sc.api_call(
            'chat.postMessage',
            channel=SLACK_ANNOUNCE_CHANNEL,
            as_user=False,
            username='civictechto-scripts',
            icon_emoji=':robot_face:',
            thread_ts=msg['ts'],
            text='test'
            )
