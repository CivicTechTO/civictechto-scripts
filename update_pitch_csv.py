import csv
import datetime
from dotenv import load_dotenv
from github import Github
import json
import os
import re
import requests
from trello import TrelloClient

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '.env')
load_dotenv(dotenv_path=filename)

TRELLO_APP_KEY = os.getenv('TRELLO_APP_KEY')
TRELLO_SECRET = os.getenv('TRELLO_SECRET')
GITHUB_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')
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

def last_hacknight(date):
    DAYS_OF_WEEK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    offset = (date.weekday() - DAYS_OF_WEEK.index('Tue')) % 7
    last_hacknight = date - datetime.timedelta(days=offset)
    return last_hacknight


PITCH_CSV_URL = 'https://raw.githubusercontent.com/CivicTechTO/dataset-civictechto-breakout-groups/master/data/civictechto-breakout-groups.csv'
r = requests.get(PITCH_CSV_URL)
pitch_csv_content = r.text

with requests.Session() as s:
    download = s.get(PITCH_CSV_URL)
    decoded_content = download.content.decode('utf-8')
    reader = csv.DictReader(decoded_content.splitlines(), delimiter=',')

    with open('projects.csv', 'w') as csvfile:
        trello_user_fieldname = 'trello_members'
        new_fieldsnames = reader.fieldnames.insert(3, trello_user_fieldname)
        writer = csv.DictWriter(csvfile, fieldnames=reader.fieldnames)
        writer.writeheader()

        hacknight_date = last_hacknight(datetime.date.today())

        for row in reader:
            # If entries for this date already exist, ignore them and rewrite.
            if row['date'] == hacknight_date.strftime('%Y-%m-%d'):
                continue
            writer.writerow(row)


        for card in cards:
            assigned_members = [client.get_member(member_id) for member_id in card.member_ids]
            usernames = [member.username for member in assigned_members]
            data = {
                    'date':    hacknight_date,
                    'project': card.name,
                    trello_user_fieldname:  ','.join(usernames),
                    }
            writer.writerow(data)

g = Github(GITHUB_TOKEN)
path = 'data/civictechto-breakout-groups.csv'
message = 'Updated data for {} hacknight.'.format(hacknight_date)
content = ''
sha = ''
g.get_user('civictechto').get_repo('dataset-civictechto-breakout-groups').update_file(path, message, content, sha)
