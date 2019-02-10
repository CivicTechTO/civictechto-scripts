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
  - [`move_trello_cards.py`](#move_trello_cardspy)
  - [`update_pitch_csv.py`](#update_pitch_csvpy)
  - [`notify_slack_pitches.py`](#notify_slack_pitchespy)
  - [`notify_slack_roles.py`](#notify_slack_rolespy)
  - [`gsheet2meetup.py`](#gsheet2meetuppy)
  - [`gsheet2shortlinks.py`](#gsheet2shortlinkspy)
  - [`grant_gdrive_perms.py`](#grant_gdrive_permspy)
  - [`send_monthly_project_email.py`](#send_monthly_project_emailpy)
  - [`next-meetup` command](#next-meetup-command)
  - [`upload2gdrive` command](#upload2gdrive-command)
- [Local Development](#computer-local-development)

## About these Automated Scripts

Some of these scripts are automatically run before and after hacknight,
using CircleCI's workflow feature. The schedule is set in the
[`.circleci/config.yml`][circleci-config] file within this repo.

Here's a diagram showing how project pitch information flows into, through and out of the Trello board, in part via scripts:

<sub>(Click to see expanded view.)</sub><br/>
[![Process Flow Diagram](https://docs.google.com/drawings/d/e/2PACX-1vSNrFFElzvRuHQM44PU--wO3kyDwhR54gnj6mHoXbJ_1CkRzgB2murOhFNM9DxIcnYSYGSk5naJH2p5/pub?w=600)](https://docs.google.com/drawings/d/1h9hY9eyfZzdVbIu-4pihQ6RBgrjj8PbUsHE4oHbGYUY/edit)

## Technologies Used

- **Python.** A programming langauge common in scripting.
- [**Click.**][click] A Python library for writing simple command-line
  tools.
- [**CircleCI.**][circleci] A script-running service that [runs scheduled
  tasks][circleci-cron] for us in the cloud.
- [**Trello.**][trello] A flexible organizing and project management
  tool that we [use to track breakout groups][trello-board].

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

![Screenshot of Slack post](https://i.imgur.com/M1y4Yi6.png)

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

### `grant_gdrive_perms.py`

This allows granting edit/view permissions on a set of Google Drive
resources (files or folders), based on membership within a Slack
public/private channel.

```
$ python scripts/grant_gdrive_perms.py --help

Usage: grant_gdrive_perms.py [OPTIONS]

  Grant Google Docs file permissions based on Slack channel membership.

  Note: The Slack API token must be issued by a user/bot with access to the
  --slack-channel provided.

Options:
  --slack-token <string>        API token for Slack (user or bot).  [required]
  --slack-channel <string>      Channel name or identifier. Example: #my-chan,
                                my-chan, C1234ABYZ, G1234ABYZ  [required]
  --google-creds <filepath>     Credentials file for Google API access
                                [required]
  --permission-file <filepath>  Path to plaintext config file listing docs and
                                permissions  [required]
  -y, --yes                     Skip confirmation prompts
  -d, --debug                   Show full debug output
  --noop                        Skip API calls that change/destroy data
  -h, --help                    Show this message and exit.
```

WIP: Runs nightly at 4am ET.

### `send_monthly_project_email.py`

This take data from the [historical dataset of breakout
groups][breakout-dataset] (generated via [`update_pitch_csv.py`](#update_pitch_csvpy)), and sends out a MailChimp update once/month, using [this MailChimp template][mailchimp-template].

This is a work in progress, and doesn't yet work or run regularly.

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
