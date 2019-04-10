import click

from commands.utils.slackclient import CustomSlackClient


CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--slack-token',
              help='API token for any Slack user.',
              envvar='SLACK_API_TOKEN',
              )
def list_dm_contacts(slack_token):
    """Generates a list of DM conversation partners.

        * Generates a list based on private and group DM's.

        * For ease, the list itself is DM'd to the user account for whom the Slack token was generated.

            * NONE of the mentioned users will be notified of this first message, since it occurs in the DM.

            * This list of usernames can be copied into new messages and modified to suit needs.
    """

    sc = CustomSlackClient(slack_token)
    res = sc.api_call('conversations.list',
        limit=100,
        types='im,mpim',
    )

    channels = res['channels']

    token_meta = sc.api_call('auth.test')

    res = sc.api_call('im.list')
    ims = res['ims']
    self_im = [c for c in ims if c['user'] == token_meta['user_id']].pop()

    recent_contacts = []

    for c in reversed(channels):
        res = sc.api_call('conversations.members',
                          limit=100,
                          channel=c['id'],
                          )
        members = res['members']
        for mid in members:
            check_by_id = lambda id: any(c['id'] == id for c in recent_contacts)
            if not check_by_id(mid):
                res = sc.api_call('users.info', user=mid)
                user = res['user']
                if not user['is_bot']:
                    recent_contacts.append(user)

    message = ''
    for u in recent_contacts:
        name_link = '<@{}> '.format(u['id'])
        message += name_link

    res = sc.api_call('chat.postMessage', channel=self_im['id'], text=message)

if __name__ == '__main__':
    list_dm_contacts()
