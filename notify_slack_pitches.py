from dotenv import load_dotenv
import os
import pystache
import re
import sys
from trello import TrelloClient

from commands.slackclient import CustomSlackClient

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '.env')
load_dotenv(dotenv_path=filename)

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

DEBUG = str2bool(os.getenv('DEBUG', ''))
SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN')
SLACK_ANNOUNCE_CHANNEL = os.getenv('SLACK_ANNOUNCE_CHANNEL_PUB')
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

def process_card(card):
    data = {
            'name': card.name,
            'chat_room': '',
            'pitcher': '',
            }

    attachments = card.get_attachments()
    chat_re = re.compile('^(?:slack|chat): (\S+)$', flags=re.IGNORECASE)
    chat_attachments = [a for a in attachments if chat_re.match(a.name)]
    if chat_attachments:
        data['chat_room'] = chat_re.match(chat_attachments.pop(0).name).group(1)

    comments = card.get_comments()
    comments.reverse()
    pitcher_re = re.compile('pitchers?:? ?(.+)', flags=re.IGNORECASE)
    # Get most recent pitcher
    # TODO: Check whether comment made in past week.
    for c in comments:
        match = pitcher_re.match(c['data']['text'])
        if match:
            pitcher_raw = match.group(1)
            data['pitcher'] = pitcher_raw
            break

    return data

# Assume Trello not used this week
if len(cards) < 3:
    sys.exit()

for i, card in enumerate(cards):
    cards[i] = process_card(card)


thread_template = open('templates/notify_slack_pitches.txt').read()
thread_content = pystache.render(thread_template, {'projects': cards})

if DEBUG or not SLACK_API_TOKEN:
    print(thread_content)
else:
    sc = CustomSlackClient(SLACK_API_TOKEN)
    sc.bot_thread(
        channel=SLACK_ANNOUNCE_CHANNEL,
        thread_content=thread_content,
    )
