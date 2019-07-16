from dotenv import load_dotenv
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import pystache
import re
from slackclient import SlackClient


dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '.env')
load_dotenv(dotenv_path=filename)

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

DEBUG = str2bool(os.getenv('DEBUG', ''))
SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN')
SLACK_ANNOUNCE_CHANNEL = os.getenv('SLACK_ANNOUNCE_CHANNEL_ORG')

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('service-key.json', scope)

gc = gspread.authorize(credentials)

role_sheet_url = 'https://docs.google.com/spreadsheets/d/1v9xUqaSqgvDDlTpFqWtBXDPLKw6HsaFU5DfSO0d_9_0/edit#gid=351752992'
sh = gc.open_by_url(role_sheet_url)
worksheet = sh.get_worksheet(0)

this_month = datetime.date.today().strftime('%b %Y')
header_row = worksheet.row_values(1)
this_month_col = header_row.index(this_month) + 1
this_month_roles = worksheet.col_values(this_month_col)
roles_col = worksheet.col_values(1)
term_col = worksheet.col_values(2)
data = {}
for i in range(len(term_col)):
    if re.match(r"1 ?mo.*", term_col[i]):
        if this_month_roles[i]:
            data.update({roles_col[i]: this_month_roles[i]})
        else:
            data.update({roles_col[i]: 'HALP WANTED :woman-raising-hand: <-- You?'})

mustache_data = [{"role": k, "organizer": v} for k,v in data.items()]

template = """
:ctto: :ctto: :ctto: :ctto: :ctto:

Who's signed up for this month's hacknight roles? These heroes!

{{#roles}}
:small_blue_diamond: *{{{ role }}}:* {{{ organizer }}}
{{/roles}}
"""

if DEBUG or not SLACK_API_TOKEN:
    print(pystache.render(template.strip(), {'roles': mustache_data}))
else:
    sc = SlackClient(SLACK_API_TOKEN)
    msg = sc.api_call(
            'chat.postMessage',
            channel=SLACK_ANNOUNCE_CHANNEL,
            as_user=False,
            username='civictechto-scripts',
            icon_emoji=':robot_face:',
            link_names=1,
            unfurl_links=False,
            text=pystache.render(template.strip(), {'roles': mustache_data})
            )
    sc.api_call(
            'chat.postMessage',
            channel=SLACK_ANNOUNCE_CHANNEL,
            as_user=False,
            username='civictechto-scripts',
            icon_emoji=':robot_face:',
            thread_ts=msg['ts'],
            link_names=1,
            unfurl_links=False,
            text='Hacknight Roles spreadsheet: https://docs.google.com/spreadsheets/d/1v9xUqaSqgvDDlTpFqWtBXDPLKw6HsaFU5DfSO0d_9_0/edit#gid=351752992'
            )
    sc.api_call(
            'chat.postMessage',
            channel=SLACK_ANNOUNCE_CHANNEL,
            as_user=False,
            username='civictechto-scripts',
            icon_emoji=':robot_face:',
            thread_ts=msg['ts'],
            link_names=1,
            unfurl_links=False,
            text='Curious how this message gets posted? https://github.com/civictechto/civictechto-scripts#readme'
            )
