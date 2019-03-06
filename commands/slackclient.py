import re

from slackclient import SlackClient

class CustomSlackClient(SlackClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def bot_message(self, channel, text, thread_ts=None):
        kwargs = {
            'channel': channel,
            'as_user': False,
            'username': 'civictechto-scripts',
            'icon_emoji': ':robot_face:',
            # Ensures that we can do our own link markup.
            'parse': 'none',
            # Parses channel names and some usernames.
            'link_names': 1,
            'link_urls': 1,
            'unfurl_links': False,
            'text': text,
        }
        if thread_ts:
            kwargs.update({'thread_ts': thread_ts})

        msg = self.api_call(
            'chat.postMessage',
            **kwargs,
            )
        return msg

    def bot_thread(self, channel, thread_content):
        # We split one text file into a thread of messages.
        messages = re.split('[\r\n]+---[-]*[\r\n]+', thread_content)
        created = []
        for m in messages:
            kwargs = {
                'channel': channel,
                'text': m,
            }
            if created:
                kwargs.update({'thread_ts': created[-1]['ts']})

            res = self.bot_message(**kwargs)
            created.append(res)
