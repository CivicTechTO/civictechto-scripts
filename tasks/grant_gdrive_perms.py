import click
import pprint
import re
from slackclient import SlackClient

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

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
@click.option('--debug', '-d',
              is_flag=True,
              help='Show full debug output',
              default=False)
@click.option('--noop',
              help='Skip API calls that change/destroy data',
              is_flag=True)
def grant_gdrive_perms(slack_token, slack_channel, google_creds, permission_file, yes, debug, noop):
    """Create/update Rebrandly shortlinks from a Google Docs spreadsheet.

    Note: The Slack API token must be issued by a user/bot with access to the --slack-channel provided.
    """

    if debug: click.echo('>>> Debug mode: enabled')

    if noop: click.echo('>>> No-op mode: enabled (No operations affecting data will be run)')

    sclient = SlackClient(slack_token)
    channel_member_emails = []

    # Get list of users in #organizing-priv

    # For each gdrive resource

        # Get list of google users with access

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
            raise click.ClickException('Channel not found in team: #' + slack_channel)
        channel = channel[0]
        channel_name = channel['name']

    click.echo('Fetching emails for members of channel {}'.format(channel_name))
    res = sclient.api_call(
        'conversations.members',
        channel='G08V58H6Y',
    )
    if not res['ok']:
        raise click.ClickException('Slack API error - ' + res['error'])
    member_ids = res['members']
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

        email = user['profile'].get('email')
        if email:
            channel_member_emails.append(email)
        else:
            click.echo('NO EMAIL: ' + pprint.pformat(user))

    click.echo(pprint.pformat(channel_member_emails))

    if noop: click.echo('Command exited no-op mode without creating/updating any data.')

if __name__ == '__main__':
    grant_gdrive_perms(auto_envvar_prefix='CTTO')
