# See: https://github.com/jonathandion/awesome-emails#templates
#
# 1. Get the CSV of pitch dataset, and filter for past month.
#
# 1. Fetch the template with default section content
#
#      GET /templates/{template_id}/default-content
#
# 1. Rebuild project section with data from CSV
#
# 1. Create campaign, and schedule to send later
#
#      POST /campaigns
#
# 1. Replace the template sections with data
#
#      PUT /campaigns/{campaign_id}/content
#
# 1. Schedule the campaign to send
#
#      POST /campaigns/{campaign_id}/actions/schedule
#
# 1. Notify slack of the scheduled campaign with archive_url to preview.

from datetime import datetime, timedelta
from jinja2 import Template
from mailchimp3 import MailChimp
import os
import pystache
import pytz

from commands.utils.slackclient import CustomSlackClient


def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

DEBUG = str2bool(os.getenv('DEBUG', ''))
MAILCHIMP_API_KEY = os.getenv('MAILCHIMP_API_KEY')
MAILCHIMP_API_USER = os.getenv('MAILCHIMP_API_USER')
MAILCHIMP_LIST_ID = os.getenv('MAILCHIMP_LIST_ID')
MAILCHIMP_TEMPLATE_ID = int(os.getenv('MAILCHIMP_TEMPLATE_ID'))
MAILCHIMP_SECTION_NAME = os.getenv('MAILCHIMP_SECTION_NAME')
SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN')
SLACK_ANNOUNCE_CHANNEL = os.getenv('SLACK_ANNOUNCE_CHANNEL_ORG')

def get_project_data():
    projects = [
            {
                'name': 'HomeTO',
                'tags': [
                    'working group',
                    ],
                'description': 'We empower at risk, low income, and homeless individuals through inclusive digital tools.',
                },
            {
                'name': 'Women and Color',
                'tags': [
                    'working group',
                    ],
                'description': 'Online community of talented women and people of colour available for speaking opportunities at tech-related events. We’ve launched! We are now planning to expand into more cities in Canada and the USA.',
                },
            {
                'name': 'Civic Tech 101',
                'tags': [
                    'learning group',
                    ],
                'description': 'Introduce you to Civic Tech Toronto and learn about one another. Please go here if it’s your first time!',
                },
            ]

    return projects

projects = get_project_data()

mc_client = MailChimp(mc_api=MAILCHIMP_API_KEY, mc_user=MAILCHIMP_API_USER)

template = mc_client.templates.default_content.all(template_id=MAILCHIMP_TEMPLATE_ID)

sections_data = template['sections']

# TODO

template = """
{%- if learning_groups -%}
<h2>Learning Groups</h2>
<ul>
  {%- for group in learning_groups %}
  <li>
    <strong>{{ group.name }}.</strong>
    {{ group.description }}
  </li>
  {%- endfor %}
</ul>
{%- endif %}

{% if working_groups -%}
<h2>Working Groups</h2>
<ul>
  {%- for group in working_groups %}
  <li>
    <strong>{{ group.name }}.</strong>
    {{ group.description }}
  </li>
  {%- endfor %}
</ul>
{%- endif -%}
"""

template = Template(template.strip())

context = {
        'learning_groups': [p for p in projects if 'learning group' in p['tags']],
        'working_groups': [p for p in projects if 'working group' in p['tags']],
        }

content = template.render(**context)

if DEBUG:
    print(content)
    exit(0)

sections_data['projects'] = content

campaign_data = {
        'recipients': {
            'list_id': MAILCHIMP_LIST_ID,
            },
        'settings': {
            'subject_line': 'Pitch recap for {}'.format('March'),
            'from_name': 'Civic Tech Toronto',
            'reply_to': 'hi@civictech.ca',
            'template_id': MAILCHIMP_TEMPLATE_ID,
            },
        'type': 'regular',
        }
campaign = mc_client.campaigns.create(campaign_data)

content_data = {
        'template': {
            'id': MAILCHIMP_TEMPLATE_ID,
            'sections': sections_data,
            }
        }
mc_client.campaigns.content.update(campaign_id=campaign['id'], data=content_data)

def calculate_send_time():
    d = timedelta(days=1)
    send_time = datetime.utcnow().replace(tzinfo=pytz.utc) + d
    return send_time

send_time = calculate_send_time()
rounded_send_time = send_time.replace(minute=15*(send_time.minute // 15))
mc_client.campaigns.actions.schedule(campaign_id=campaign['id'], data={'schedule_time': rounded_send_time})

list_data = mc_client.lists.get(MAILCHIMP_LIST_ID)

tmpl_vars = {
    'subscriber_count': list_data['stats']['member_count'],
    # TODO: Convert this time from UTC to ET
    'send_date': rounded_send_time.strftime('%a, %b %-m @ %-I:%M') + rounded_send_time.strftime('%p').lower(),
    'preview_url': campaign['archive_url'],
}
thread_template = open('templates/send_monthly_project_email.txt').read()
thread_content = pystache.render(thread_template, tmpl_vars)

if DEBUG or not SLACK_API_TOKEN:
    print(thread_content)
else:
    sc = CustomSlackClient(SLACK_API_TOKEN)
    sc.bot_thread(
        channel=SLACK_ANNOUNCE_CHANNEL,
        thread_content=thread_content,
    )
