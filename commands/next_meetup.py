import click
import meetup.api
import re

try:
    import commands.common as common
except ImportError:
    # Allow running file as standalone
    import common

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

common_params = common.common_params

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--meetup-api-key',
              required=True,
              help='API key for member of leadership team',
              envvar=common.prefix_envvar('MEETUP_API_KEY'),
              metavar='<string>')
@click.option('--meetup-group-slug',
              required=True,
              help='Meetup group name from URL',
              envvar=common.prefix_envvar('MEETUP_GROUP_SLUG'),
              metavar='<string>')
@click.option('--filter',
              default='',
              help='String or pattern to match on event title, for seeking next event. Case-insensitive. Default: None.',
              metavar='<string|regex>',
              )
@click.option('--fields',
              default='event_url',
              help='Comma-separated list of event fields to return. Default: event_url',
              metavar='<one,two>',
              )
@common_params
def next_meetup(meetup_api_key, meetup_group_slug, filter, fields, yes, verbose, debug, noop):
    """Get the next event for a given Meetup group.

        * Can be filtered based on event title.
        * Can echo any event fields from the Meetup API response.
    """

    if not filter:
        filter = '.*'

    mclient = meetup.api.Client(meetup_api_key)
    response = mclient.GetEvents({
        'group_urlname': meetup_group_slug,
        'status': 'upcoming',
    })
    upcoming_events = response.results

    event_title_re = re.compile(filter, flags=re.IGNORECASE)
    for e in upcoming_events:
        if re.match(event_title_re, e['name']):
            next_event = e
            break

    common.echo_config(next_event, fields.split(','))

if __name__ == '__main__':
    next_meetup()
