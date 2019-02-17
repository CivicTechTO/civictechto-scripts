import click
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials
import pprint
import re
from slackclient import SlackClient

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/drive']

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
              help='Path to plaintext config file listing docs and permissions',
              metavar='<filepath>')
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

    sclient = SlackClient(slack_token)

    # Get list of users in #organizing-priv

    # Resolve channel name.
    chan_id_re = re.compile('^(G|C)[A-Z0-9-_]+$')
    if re.match(chan_id_re, slack_channel):
        res = sclient.api_call(
            'conversations.info',
            channel=slack_channel,
        )
        if not res['ok']:
            raise click.ClickException('Slack API error - ' + res['error'])
        channel = res['channel']
    else:
        # Strip the hash symbol from front
        slack_channel = slack_channel.replace('#', '')
        res = sclient.api_call(
            'conversations.list',
            exclude_archived=True,
            # TODO: Instead support pagination.
            limit=1000,
            types='public_channel,private_channel',
        )
        if not res['ok']:
            raise click.ClickException('Slack API error - ' + res['error'])
        channel = [c for c in res['channels'] if c['name'] == slack_channel]
        if not channel:
            raise click.ClickException('Channel not found in team: ' + slack_channel)
        channel = channel[0]
        channel_name = channel['name']

    click.echo('Fetching member emails within channel #{}'.format(channel_name))
    res = sclient.api_call(
        'conversations.members',
        channel=channel['id'],
    )
    if not res['ok']:
        raise click.ClickException('Slack API error - ' + res['error'])
    member_ids = res['members']
    members = []
    for mid in member_ids:
        res = sclient.api_call(
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

    members.append({'profile': {'email': 'sfdkmlsfdlkjfsa@mailinator.com'}})

    # Get permissiosn of GDrive resources
    credentials = ServiceAccountCredentials.from_json_keyfile_name(google_creds, GOOGLE_SCOPES)
    if debug: click.echo('>>> Service account email: ' + credentials.service_account_email)
    service = build('drive', 'v2', credentials=credentials)
    test_file = '1i7S3tlQgbON7rkL3ThWcoiArXRafO4-VV9e8rM3WmXY'
    file_ids = []
    file_ids.append(test_file)
    for fid in file_ids:
        file = service.files().get(fileId=fid).execute()
        if verbose:
            click.echo("Preparing to modify permissions on '{}': {}".format(file['title'], file['alternateLink']), err=True)
        res = service.permissions().list(fileId=file['id']).execute()
        perms = res['items']
        perms = [p for p in perms if not p['deleted']]
        perms = [p for p in perms if p['type'] == 'user']
        for m in members:
            email = m['profile']['email']
            role = 'writer'
            existing_perm = [p for p in perms if p['emailAddress'] == email]
            if existing_perm:
                existing_perm = existing_perm.pop()

            if existing_perm:
                if existing_perm['role'] == 'owner':
                    click.echo('>>> Skipped {} permission: {} (user is already owner)'.format(role, email), err=True)
                    continue
                if existing_perm['role'] == role:
                    click.echo('>>> Skipped {} permission: {} (proper role already set)'.format(role, email), err=True)
                    continue
                output = '>>> Updated {} permission: {}'
            else:
                output = '>>> Added {} permission: {}'

            try:
                res = service.permissions().insert(fileId=fid, sendNotificationEmails=False, body={'role': role, 'type': 'user', 'value': email}).execute()
                if verbose:
                    click.echo(output.format(role, email), err=True)
            except HttpError as e:
                if int(e.resp.status) == 400:
                    res = json.loads(e.content)
                    error = res['error']['errors'][0]
                    if error['reason'] == 'invalidSharingRequest':
                        res = service.permissions().insert(fileId=fid, sendNotificationEmails=True, body={'role': role, 'type': 'user', 'value': email}).execute()
                        if verbose:
                            click.echo(">>> Added {} permission: {} (Sending email as no associated Google account)".format(role, email), err=True)
                else:
                    raise

        # Get list of google users with access

    if noop: click.echo('Command exited no-op mode without creating/updating any data.')

if __name__ == '__main__':
    grant_gdrive_perms(auto_envvar_prefix='CTTO')
