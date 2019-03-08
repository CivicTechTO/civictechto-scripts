import csv
import itertools
import re
import requests
import time


class BreakoutGroup(object):
    CHAT_RE = re.compile('^(?:slack|chat): (\S+)$', flags=re.IGNORECASE)
    PITCHER_RE = re.compile('pitchers?:? ?(.+)', flags=re.IGNORECASE)
    NONCE = int(time.time())

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
        dataset_url = 'https://raw.githubusercontent.com/CivicTechTO/dataset-civictechto-breakout-groups/master/data/civictechto-breakout-groups.csv?r={}'.format(self.NONCE)
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
