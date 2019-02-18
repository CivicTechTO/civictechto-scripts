import click
import csv
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials
import os
import pprint
import re
from slackclient import SlackClient
import urllib
import yaml


CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/drive']
CHAN_ID_RE = re.compile('^(G|C)[A-Z0-9-_]+$')

def get_state(state):
    filename = os.path.basename(__file__)
    filename = os.path.splitext(filename)[0]

    yaml.Dumper.ignore_aliases = lambda *args: True
    output = yaml.dump({filename: state}, default_flow_style=False)
    return output

class MySlackClient(SlackClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_channel(self, id_or_name):
        if re.match(CHAN_ID_RE, id_or_name):
            res = self.api_call(
                'conversations.info',
                channel=id_or_name,
            )
            if not res['ok']:
                raise click.ClickException('Slack API error - ' + res['error'])

            return channel
        else:
            # Strip the hash symbol from front
            chan_name = id_or_name.replace('#', '')
            res = self.api_call(
                'conversations.list',
                exclude_archived=True,
                # TODO: Instead support pagination.
                limit=1000,
                types='public_channel,private_channel',
            )
            if not res['ok']:
                raise click.ClickException('Slack API error - ' + res['error'])
            channel = [c for c in res['channels'] if c['name'] == chan_name]
            if not channel:
                raise click.ClickException('Channel not found in team: ' + chan_name)

            return channel[0]

    def get_channel_member_ids(self, chan_id):
        res = self.api_call(
            'conversations.members',
            channel=chan_id,
        )
        if not res['ok']:
            raise click.ClickException('Slack API error - ' + res['error'])

        member_ids = res['members']
        return member_ids

    def get_real_channel_members(self, chan_id):
        member_ids = self.get_channel_member_ids(chan_id)
        members = self.get_real_members(member_ids)
        return members

    def get_real_members(self, member_ids):
        members = []
        for mid in member_ids:
            res = self.api_call(
                'users.info',
                user=mid
            )
            if not res['ok']:
                raise click.ClickException('Slack API error - ' + res['error'])
            user = res['user']
            if user['is_bot']:
                continue

            if not user['profile'].get('email'):
                continue

            members.append(user)

        return members

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--slack-token',
              required=True,
              help='API token for Slack (user or bot).',
              metavar='<string>')
@click.option('--slack-channel',
              required=True,
              help='Channel name or identifier. Example: #my-chan, my-chan, C1234ABYZ, G1234ABYZ',
              metavar='<string>')
@click.option('--google-creds',
              required=True,
              help='Credentials file for Google API access',
              metavar='<filepath>')
@click.option('--permission-file',
              required=True,
              help='Path to plaintext CSV file listing docs and permissions',
              metavar='<file>')
@click.option('--yes', '-y',
              help='Skip confirmation prompts',
              is_flag=True)
@click.option('--verbose', '-v',
              help='Show output for each action',
              is_flag=True)
@click.option('--debug', '-d',
              is_flag=True,
              help='Show full debug output',
              default=False)
@click.option('--noop',
              help='Skip API calls that change/destroy data',
              is_flag=True)
def grant_gdrive_perms(slack_token, slack_channel, google_creds, permission_file, yes, verbose, debug, noop):
    """Grant Google Docs file permissions based on Slack channel membership.

    Note: The Slack API token must be issued by a user/bot with access to the --slack-channel provided.
    """

    if debug: click.echo('>>> Debug mode: enabled')

    if noop: click.echo('>>> No-op mode: enabled (No operations affecting data will be run)')

    sclient = MySlackClient(slack_token)

    # TODO: Warn about non-private groups.
    channel = sclient.get_channel(slack_channel)

    click.echo('Checking members within channel #{}'.format(channel['name']))
    members = sclient.get_real_channel_members(channel['id'])

    # TODO: Remove this.
    members.append({'profile': {'email': 'sfdkmlsfdlkjfsa@mailinator.com'}})
    # TODO: Fix this to be per-file.
    state = {
        'members': {
            'added': [],
            'updated': [],
            'unchanged': [],
        },
    }

    # Get permissiosn of GDrive resources
    credentials = ServiceAccountCredentials.from_json_keyfile_name(google_creds, GOOGLE_SCOPES)
    if debug: click.echo('>>> Service account email: ' + credentials.service_account_email)
    service = build('drive', 'v2', credentials=credentials)

    def get_csv_rows(file):
        # TODO: Handle URLs too
        with open(file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                yield row

    def get_gdrive_resource_key(url):
        url_data = urllib.parse.urlsplit(url)
        if url_data.netloc == '':
            return url_data.path
        if url_data.netloc == 'drive.google.com':
            return url_data.path.split('/')[-1]
        if url_data.netloc == 'docs.google.com':
            return url_data.path.split('/')[-2]
        return ''

    for r in get_csv_rows(permission_file):
        fid = get_gdrive_resource_key(r['resource_url'])
        if not fid:
            click.echo('Skipping: ' + r['resource_url'])
            continue
        file = service.files().get(fileId=fid).execute()
        if verbose:
            click.echo("Preparing to modify permissions on '{}': {}".format(file['title'], file['alternateLink']), err=True)
        res = service.permissions().list(fileId=file['id']).execute()
        perms = res['items']
        perms = [p for p in perms if not p.get('deleted')]
        perms = [p for p in perms if p['type'] == 'user']
        for m in members:
            email = m['profile']['email']
            role = r['permission']
            existing_perm = [p for p in perms if p['emailAddress'] == email]
            if existing_perm:
                existing_perm = existing_perm.pop()

            if existing_perm:
                if existing_perm['role'] == 'owner':
                    click.echo('>>> Skipped {} permission: {} (user is already owner)'.format(role, email), err=True)
                    state['members']['unchanged'].append(m)
                    continue
                if existing_perm['role'] == role:
                    click.echo('>>> Skipped {} permission: {} (proper role already set)'.format(role, email), err=True)
                    state['members']['unchanged'].append(m)
                    continue
                output = '>>> Updated {} permission: {}'
                state['members']['updated'].append(m)
            else:
                output = '>>> Added {} permission: {}'
                state['members']['added'].append(m)

            try:
                if not noop:
                    res = service.permissions().insert(fileId=fid, sendNotificationEmails=False, body={'role': role, 'type': 'user', 'value': email}).execute()
                if verbose:
                    click.echo(output.format(role, email), err=True)
            except HttpError as e:
                if int(e.resp.status) == 400:
                    res = json.loads(e.content)
                    error = res['error']['errors'][0]
                    if error['reason'] == 'invalidSharingRequest':
                        if not noop:
                            res = service.permissions().insert(fileId=fid, sendNotificationEmails=True, body={'role': role, 'type': 'user', 'value': email}).execute()
                        if verbose:
                            click.echo(">>> Added {} permission: {} (Sending email as no associated Google account)".format(role, email), err=True)
                else:
                    raise

    echo_state = False
    if echo_state:
        click.echo(get_state(state))

    if noop: click.echo('Command exited no-op mode without creating/updating any data.')

if __name__ == '__main__':
    grant_gdrive_perms(auto_envvar_prefix='CTTO')
