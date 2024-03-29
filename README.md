# CivicTechTO Scripts
[![Run scripts](https://img.shields.io/badge/scheduled%20scripts-RUN-44cc11.svg)][circleci-proj]
[![CircleCI Status](https://img.shields.io/circleci/project/github/CivicTechTO/civictechto-scripts.svg?label=CircleCI)][circleci-proj]

Helper scripts for CivicTechTO organizing tasks.

We use this as a catch-all for simple scripts that help with organizing
tasks. Many of them run automatically each week.

## Contents

- [About This Repo](#about-these-automated-scripts)
- [Technologies Used](#technologies-used)
- **Scripts**
  - [`notify_slack_pitches.py`](#notify_slack_pitchespy)
  - [`gsheet2meetup.py`](#gsheet2meetuppy)
  - [`send_monthly_project_email.py`](#send_monthly_project_emailpy)
  - [`next-meetup` command](#next-meetup-command)
  - [`upload2gdrive` command](#upload2gdrive-command)
  - [`announce-booking-status` command](#announce-booking-status-command)
  - [`update-member-roster` command](#update-member-roster-command)
  - [`list_dm_partners.py`](#list_dm_partnerspy)
- [Local Development](#computer-local-development)

| Trigger | Description | Script :link: Docs | Status :link: Logs |
|---------|-------------|---------------------|--------------------|
| Nightly | Update shortlinks from gsheet | [`gsheet2shortlinks.py`](#gsheet2shortlinkspy) | [![Logs: Update Shortlinks][shortlinks-badge]][shortlinks-logs]
| Day Before | Announce roles in #organizing-open | [`notify_slack_roles.py`](#notify_slack_rolespy) | [![Logs: Notify Slack Roles][roles-badge]][roles-logs]
| Pre-Hacknight | Reset Trello pitch column | [`move_trello_cards.py`](#move_trello_cardspy) | [![Logs: Reset Pitches][reset-badge]][reset-logs]
| Post-Hacknight | Save pitch info to dataset | [`update_pitch_csv.py`](#update_pitch_csvpy) | [![Logs: Save Pitch Data][data-badge]][data-logs]
| Save Pitch Data | Announce pitches in #general | [`notify_slack_pitches.py`](#notify_slack_pitchespy) | [![Logs: Notify Slack Pitches][pitches-badge]][pitches-logs]

   [shortlinks-badge]: https://github.com/CivicTechTO/civictechto-scripts/actions/workflows/action--update-shortlinks.yml/badge.svg
   [shortlinks-logs]: https://github.com/CivicTechTO/civictechto-scripts/actions/workflows/action--update-shortlinks.yml
   [roles-badge]: https://github.com/CivicTechTO/civictechto-scripts/actions/workflows/action--notify-slack-roles.yml/badge.svg
   [roles-logs]: https://github.com/CivicTechTO/civictechto-scripts/actions/workflows/action--notify-slack-roles.yml
   [reset-badge]: https://github.com/CivicTechTO/civictechto-scripts/actions/workflows/action--reset-pitches.yml/badge.svg
   [reset-logs]: https://github.com/CivicTechTO/civictechto-scripts/actions/workflows/action--reset-pitches.yml
   [data-badge]: https://github.com/CivicTechTO/civictechto-scripts/actions/workflows/action--save-pitch-data.yml/badge.svg
   [data-logs]: https://github.com/CivicTechTO/civictechto-scripts/actions/workflows/action--save-pitch-data.yml
   [pitches-badge]: https://github.com/CivicTechTO/civictechto-scripts/actions/workflows/action--notify-slack-pitches.yml/badge.svg
   [pitches-logs]: https://github.com/CivicTechTO/civictechto-scripts/actions/workflows/action--notify-slack-pitches.yml

## About these Automated Scripts

Some of these scripts are automatically run before and after hacknight,
using CircleCI's workflow feature.
(Update: A migration from CircleCI to GitHub Actions is in progress.)
The schedule is set in the [`.circleci/config.yml`][circleci-config] file within this repo.

Here's a diagram showing how project pitch information flows into, through and out of the Trello board, in part via scripts:

<sub>(Click to see expanded view.)</sub><br/>
[![Process Flow Diagram](https://docs.google.com/drawings/d/e/2PACX-1vSNrFFElzvRuHQM44PU--wO3kyDwhR54gnj6mHoXbJ_1CkRzgB2murOhFNM9DxIcnYSYGSk5naJH2p5/pub?w=600)](https://docs.google.com/drawings/d/1h9hY9eyfZzdVbIu-4pihQ6RBgrjj8PbUsHE4oHbGYUY/edit)

## Technologies Used

- **Python.** A programming langauge common in scripting.
- [**Click.**][click] A Python library for writing simple command-line
  tools.
- [**CircleCI.**][circleci] A script-running service that [runs scheduled
  tasks][circleci-cron] for us in the cloud. (Deprecated)
- [**GitHub Actions.**][github-actions] A script-running service that runs scheduled tasks for us in the cloud. (Incoming)
- [**Trello.**][trello] A flexible organizing and project management
  tool that we [use to track breakout groups][trello-board].
- [**`CivicTechTO/circleci-job-runner`.**][job-runner] Simple API for starting safe CircleCI jobs via public endpoints. (Needs update)

[job-runner]: https://github.com/CivicTechTO/circleci-job-runner
[github-actions]: https://github.com/features/actions

## :computer: Local Development

These scripts are designed to run in the cloud, using code from the
`master` branch on GitHub. However, they can also be run on a local
workstation.  Further, contributions should be tested locally before
pushing changes to repo, as changes to existing scripts on `master` will
then come into effect.

### Setup

We recommend using `pipenv` for isolating your Python
environment. After installing, just follow these steps.

1. Install the required packages:

    ```sh
    # Run this only first-time or after pulling git changes.
    $ pipenv install
    # Run this at the start of each terminal session.
    $ pipenv shell
    ```

2. Copy the configuration file:

    ```
    $ cp sample.env .env
    ```

3. Edit the file according to its comments. (Some scripts can take
   command-line args directly.)

## Scripts

### `move_trello_cards.py`

On the [Trello board][trello-board], this moves all cards from one list to another.

> eg. `Tonight's Pitches` :arrow_right: `Recently Pitched`

Runs pre-hacknight.

```
$ pipenv run python move_trello_cards.py --help

Usage: move_trello_cards.py [OPTIONS]

Options:
  -k, --api-key TEXT     Trello API key.  [required]
  -s, --api-secret TEXT  Trello API token/secret.  [required]
  -f, --from-list TEXT   Name or ID of Trello list which cards are moved FROM.
                         [required]
  -t, --to-list TEXT     Name or ID of Trello list which cards are moved INTO.
                         [required]
  -b, --board TEXT       ID of Trello board on which to act.  [required]
  -d, --older-than DAYS  If provided, card only moved if older than this.
                         Default: 0
  -y, --yes              Skip confirmation prompts
  -v, --verbose          Show output for each action
  -d, --debug            Show full debug output
  --noop                 Skip API calls that change/destroy data
  -h, --help             Show this message and exit.
```

### `update_pitch_csv.py`

This updates the [historical dataset of breakout
groups][breakout-dataset] who pitched each week, based on the [Trello
board][trello-board].

Runs post-hacknight.

### `notify_slack_pitches.py`

This takes data from the [Trello board][trello-board], and drops a
message in Slack's `#general` channel, announcing who pitched this week.

Runs post-hacknight.

![Screenshot of Slack post](https://i.imgur.com/mhHudig.png)

### `notify_slack_roles.py`

This takes data from the [Hacknight Roles spreadsheet][hacknight-roles-sheet], and drops a
message in Slack's `#organizing-open` channel, announcing who signed up for each hacknight-organizing role this month. If a role is unclaimed, it solicits help.

Runs day before hacknight.

![Screenshot of Slack post](https://i.imgur.com/PLUi7Lh.png)

### `gsheet2meetup.py`

This takes data from a GDrive spreadsheet ([sample][sample_sheet]), and
uses it to create/update events in a Meetup.com group. It uses a simple
template format, populated by spreadsheet columns, for the event
description ([sample][desc_template]).

   [sample_sheet]: https://docs.google.com/spreadsheets/d/19B5sk8zq_pYZVe0DMGCKKBP2jYolm6COfJfIq45vwCg/edit#gid=2098195688
   [desc_template]: examples/meetup_event_template.txt

```
$ python scripts/gsheet2meetup.py --help

Usage: gsheet2meetup.py [OPTIONS]

  Create/update events of a Meetup.com group from a Google Docs spreadsheet.

Options:
  --gsheet <url>            URL to publicly readable Google Spreadsheet,
                                including sheet ID gid  [required]
  --meetup-api-key <string>     API key for member of leadership team
                                [required]
  --meetup-group-slug <string>  Meetup group name from URL  [required]
  -y, --yes                     Skip confirmation prompt
  -d, --debug                   Show full debug output
  --noop                        Skip API calls that change/destroy data
  -h, --help                    Show this message and exit.
```

Runs nightly at 4am ET.

### `gsheet2shortlinks.py`

This takes data from a GDrive spreadsheet ([sample][sample_shortlink_sheet]), and
uses it to create/update shortlinks managed on Rebrandly.

   [sample_shortlink_sheet]: https://docs.google.com/spreadsheets/d/12VUXPCpActC77wy6Q8Khyb-iZ_nlNwshO8XswYRj5XE/edit#gid=776462093

```
$ python gsheet2shortlinks.py --help

Usage: gsheet2shortlinks.py [OPTIONS]

  Create/update Rebrandly shortlinks from a Google Docs spreadsheet.

  Here are some notes on spreadsheet columns:

      * slashtag: the shortlink component of path.

      * destination_url: where the shortlink points to.

      * If the following columns exist and a --google-creds option is
      passed, they will be updated:

          * Note: These features are not yet implemented.

          * created: date and time when the link was created and tracking
          began.

          * clicks: number of click-through since creation.

      * Extra columns will have no effect.

Options:
  --gsheet <url>                  URL to publicly readable Google Spreadsheet,
                                  including sheet ID gid  [required]
  --rebrandly-api-key <string>    API key for Rebrandly  [required]
  -d, --domain-name <example.com>
                                  Shortlink domain on Rebrandly  [required if
                                  multiple domains on account]
  -y, --yes                       Skip confirmation prompts
  -d, --debug                     Show full debug output
  --noop                          Skip API calls that change/destroy data
  -h, --help                      Show this message and exit.
```

Runs nightly at 4am ET.

### `upload2gdrive` command

This command uploads local files to a Google Drive folder.

```
$ pipenv run python cli.py upload2gdrive --help

Usage: cli.py upload2gdrive [OPTIONS] FILE

Options:
  -f, --gdrive-folder <url/id>  Google Drive folder to upload file into. (URL
                                or folder ID)  [required]
  -c, --google-creds <file>     JSON keyfile for a Google service account.
                                [required]
  -y, --yes                     Skip confirmation prompts
  -v, --verbose                 Show output for each action
  -d, --debug                   Show full debug output
  --noop                        Skip API calls that change/destroy data
  -h, --help                    Show this message and exit.
```

This command runs in conjunction with other tasks/scripts.

### `next-meetup` command

```
$ pipenv run python cli.py next-meetup --help

Usage: cli.py next-meetup [OPTIONS]

  Get the next event for a given Meetup group.

  * Can be filtered based on event title. * Can echo any event fields from
  the Meetup API response.

Options:
  --meetup-api-key <string>     API key for member of leadership team
                                [required]
  --meetup-group-slug <string>  Meetup group name from URL  [required]
  --filter <string|regex>       String or pattern to match on event title, for
                                seeking next event. Case-insensitive. Default:
                                None.
  --fields <one,two>            Comma-separated list of event fields to
                                return. Default: event_url
  -y, --yes                     Skip confirmation prompts
  -v, --verbose                 Show output for each action
  -d, --debug                   Show full debug output
  --noop                        Skip API calls that change/destroy data
  -h, --help                    Show this message and exit.
```

This command runs in conjunction with other tasks/scripts.

### `announce-booking-status` command

Reads from the [speaker booking spreadsheet][speaker-sheet] and generates a
message in Slack.

![Screenshot of posted Slack message](https://i.imgur.com/seJt18j.png)

   [speaker-sheet]: https://docs.google.com/spreadsheets/d/1-p0CyUMC0nqrEQNc6Yikd2vg033GoChSWR8rFKFxfgU/edit#gid=0

```
$ pipenv run python cli.py announce-booking-status --help

Usage: cli.py announce-booking-status [OPTIONS]

  Notify a slack channel of high-level status for upcoming event & speaker
  booking.

Options:
  --gsheet TEXT       URL to publicly readable Google Spreadsheet.  [required]
  --slack-token TEXT  API token for any Slack user.
  -c, --channel TEXT  Name or ID of Slack channel in which to announce.
                      [required]
  -y, --yes           Skip confirmation prompts
  -v, --verbose       Show output for each action
  -d, --debug         Show full debug output
  --noop              Skip API calls that change/destroy data
  -h, --help          Show this message and exit.
```

This command runs weekly after hacknight.


### `update-member-roster` command

Updates a spreadsheet ([example][roster-example]) from membership in a Slack channel (in our case,
the invite-only `#organizing-priv`). This spreadsheet is in turn
intended to be used to render a view of those members on a webpage, etc.
(Related: [`CivicTechTO/people-list-parser`][people-list-parser])

   [people-list-parser]: https://github.com/CivicTechTO/people-list-parser
   [roster-example]: https://docs.google.com/spreadsheets/d/1LCVxEXuv70R-NozOwhNxZFtTZUmn1FLMPVD5wgIor9o/edit#gid=642523045

![Screenshot of spreadsheet and rendered grid](https://i.imgur.com/24SPx5k.png)

```
$ pipenv run python cli.py update-member-roster --help
Usage: cli.py update-member-roster [OPTIONS]

  Update a spreadsheet of members based on Slack channel membership.

Options:
  --gsheet TEXT       URL to publicly readable Google Spreadsheet.
[required]
  --slack-token TEXT  API token for any Slack user.
  -c, --channel TEXT  Name or ID of Slack channel in which to fetch
                      membership.  [required]
  -y, --yes           Skip confirmation prompts
  -v, --verbose       Show output for each action
  -d, --debug         Show full debug output
  --noop              Skip API calls that change/destroy data
  -h, --help          Show this message and exit.
```

Note: Runs nightly.

### `send_monthly_project_email.py`

This take data from the [historical dataset of breakout
groups][breakout-dataset] (generated via [`update_pitch_csv.py`](#update_pitch_csvpy)), and sends out a MailChimp update once/month, using [this MailChimp template][mailchimp-template].

This is a work in progress, and doesn't yet work or run regularly.

### `list_dm_partners.py`

```
$ pipenv run python list_dm_partners.py --help

Usage: list_dm_partners.py [OPTIONS]

  Generates a list of DM conversation partners.

  * Generates a list based on private and group DM's.

  * For ease, the list itself is DM'd to the user account for whom the Slack
  token was generated.

      * NONE of the mentioned users will be notified of this first message,
      since it occurs in the DM.

      * This list of usernames can be copied into new messages and modified
      to suit needs.

Options:
  --slack-token TEXT  API token for any Slack user.
  -h, --help          Show this message and exit.
```

This script doesn't run automatically. It is intended to be run from a
local computer.

![Screenshot of Slack DM](https://i.imgur.com/Ky5oYB4.png)


<!-- Links -->
   [click]: http://click.pocoo.org/5/
   [circleci]: https://circleci.com/docs/2.0/about-circleci/
   [circleci-cron]: https://support.circleci.com/hc/en-us/articles/115015481128-Scheduling-jobs-cron-for-builds-
   [circleci-proj]: https://circleci.com/gh/CivicTechTO/civictechto-scripts
   [circleci-config]:.circleci/config.yml#L6-L31
   [breakout-dataset]: https://github.com/CivicTechTO/dataset-civictechto-breakout-groups/blob/master/data/civictechto-breakout-groups.csv
   [trello]: https://trello.com/about
   [trello-board]: https://trello.com/b/EVvNEGK5/hacknight-projects
   [hacknight-roles-sheet]: https://docs.google.com/spreadsheets/d/1v9xUqaSqgvDDlTpFqWtBXDPLKw6HsaFU5DfSO0d_9_0/edit
   [mailchimp-template]: https://us11.admin.mailchimp.com/templates/design?tid=364745
