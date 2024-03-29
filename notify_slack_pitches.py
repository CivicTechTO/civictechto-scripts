from dotenv import load_dotenv
import os
import pystache
import re
import sys
from jinja2 import Template
from trello import TrelloClient

from commands.utils.slackclient import CustomSlackClient
from commands.utils.trello import BreakoutGroup

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '.env')
load_dotenv(dotenv_path=filename)

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

DEBUG = str2bool(os.getenv('DEBUG', ''))
SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN')
SLACK_ANNOUNCE_CHANNEL = os.getenv('SLACK_ANNOUNCE_CHANNEL_PUB')
LIST_TONIGHT = "Tonight's Pitches"

# No API key needed for read-only.
client = TrelloClient(None)

board_url = 'https://trello.com/b/EVvNEGK5/hacknight-projects'
m = re.search('^https://trello.com/b/(?P<board_id>.+?)(?:/.*)?$', board_url)
board_id = m.group('board_id')

board = client.get_board(board_id)
lists = board.get_lists('open')
[pitch_list] = [l for l in lists if l.name == LIST_TONIGHT]
cards = pitch_list.list_cards()

# Assume Trello not used this week
if len(cards) < 3:
    sys.exit()

for i, card in enumerate(cards):
    cards[i] = vars(BreakoutGroup(card))

# Sort newest to top of listing
cards = sorted(cards, key=lambda i: i['pitch_count'])

thread_template = open('templates/notify_slack_pitches.txt').read()
template = Template(thread_template)
context = {
    'projects': cards,
    'maturity': {
        'new': 1,
        'level_1': 2,
        'level_2': 5,
        'level_3': 20,
    },
}
thread_content = template.render(**context)


if DEBUG or not SLACK_API_TOKEN:
    print(thread_content)
else:
    sc = CustomSlackClient(SLACK_API_TOKEN)
    sc.bot_thread(
        channel=SLACK_ANNOUNCE_CHANNEL,
        thread_content=thread_content,
    )
