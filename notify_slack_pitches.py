import csv
from dotenv import load_dotenv
import itertools
import os
import pystache
import re
import requests
import sys
import time
from trello import TrelloClient

from commands.slackclient import CustomSlackClient

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '.env')
load_dotenv(dotenv_path=filename)

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

SCRIPT_TIME = int(time.time())

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


class BreakoutGroup(object):
    CHAT_RE = re.compile('^(?:slack|chat): (\S+)$', flags=re.IGNORECASE)
    PITCHER_RE = re.compile('pitchers?:? ?(.+)', flags=re.IGNORECASE)

    card = None
    name = str()
    chat_room = str()
    pitcher = str()
    streak_count = 0
    pitch_count = 0
    is_new = False

    def __init__(self, card):
        self.card = card
        self.generate_from_trello_card()
        self._process_historical_data()

    def generate_from_trello_card(self):
        self.name = self.card.name
        self.chat_room = self._get_chat_room()
        self.pitcher = self._get_pitcher()

    def _process_historical_data(self):
        dataset_url = 'https://raw.githubusercontent.com/CivicTechTO/dataset-civictechto-breakout-groups/master/data/civictechto-breakout-groups.csv?r={}'.format(SCRIPT_TIME)
        r = requests.get(dataset_url)
        csv_content = r.content.decode('utf-8')
        csv_content = csv_content.split('\r\n')
        reader = csv.DictReader(csv_content, delimiter=',')
        # TODO: Ensure these are sorted by date.
        reverse_chron = list(reader)[::-1]

        # Tally pitch count.
        self.pitch_count = 0
        for row in reverse_chron:
            if row['trello_card_id'] == self.card.id:
                self.pitch_count += 1

        if self.pitch_count == 0:
            self.is_new = True

        # Tally streak count.
        self.streak_count = 0
        for key, group in itertools.groupby(reverse_chron, key=lambda r: r['date']):
            matches = [p for p in group if p['trello_card_id'] == self.card.id]
            if matches:
                self.streak_count += 1
                continue
            else:
                break

    def _get_chat_room(self):
        attachments = self.card.get_attachments()
        for a in attachments:
            match = self.CHAT_RE.match(a.name)
            if match:
                return match.group(1)

        return ''

    def _get_pitcher(self):
        comments = self.card.get_comments()
        comments.reverse()
        # Get most recent pitcher
        # TODO: Check whether comment made in past week.
        for c in comments:
            match = self.PITCHER_RE.match(c['data']['text'])
            if match:
                return match.group(1)

        return ''

# Assume Trello not used this week
if len(cards) < 3:
    sys.exit()

for i, card in enumerate(cards):
    cards[i] = vars(BreakoutGroup(card))

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
