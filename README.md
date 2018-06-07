# CivicTechTO Scripts
[![Run scripts](https://img.shields.io/badge/scheduled%20scripts-RUN-44cc11.svg)][circleci-proj]
[![CircleCI Status](https://img.shields.io/circleci/project/github/CivicTechTO/civictechto-scripts.svg?label=CircleCI)][circleci-proj]

Helper scripts for CivicTechTO organizing tasks.

We use this as a catch-all for simple scripts that help with organizing
tasks. Many of them run automatically each week.

## Technologies Used

- **Python.** A programming langauge common in scripting.
- [**Click.**][click] A Python library for writing simple command-line
  tools.
- [**CircleCI.**][circleci] A script-running service that [runs scheduled
  tasks][circleci-cron] for us in the cloud.
- [**Trello.**][trello] A flexible organizing and project management
  tool that we [use to track breakout groups][trello-board].

## About these Automated Scripts

Some of these scripts are automatically run before and after hacknight
using CircleCI's workflow feature. The schedule is set in the
[`.circleci/config.yml`][circleci-config] file within this repo.

## :computer: Local Development

### Setup

We recommend using `virtualenvwrapper` for isolating your Python
environment. Then just follow these steps.

1. Install the required packages:

    ```
    $ pip install -r requirements.txt
    ```

2. Copy the configuration file:

    ```
    $ cp sample.env .env
    ```

3. Edit the file according to its comments.

## Scripts

### `clean_pitch_list.py`

On the [Trello board][trello-board], this moves all cards from the pitch
list to the active column. This run prior to each hacknight.

Runs pre-hacknight.

```
python clean_pitch_list.py
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

### `notify_slack_roles.py`

This takes data from the [Hacknight Roles spreadsheet][hacknight-roles-sheet], and drops a
message in Slack's `#organizing-open` channel, announcing who pitched this week.

Runs pre-hacknight.

<!-- Links -->
   [click]: http://click.pocoo.org/5/
   [circleci]: https://circleci.com/docs/2.0/about-circleci/
   [circleci-cron]: https://support.circleci.com/hc/en-us/articles/115015481128-Scheduling-jobs-cron-for-builds-
   [circleci-proj]: https://circleci.com/gh/civictechto/civictechto-scripts
   [circleci-config]:.circleci/config.yml#L126
   [breakout-dataset]: https://github.com/CivicTechTO/dataset-civictechto-breakout-groups/blob/master/data/civictechto-breakout-groups.csv
   [trello]: https://trello.com/about
   [trello-board]: https://trello.com/b/EVvNEGK5/hacknight-projects
   [hacknight-roles-sheet]: https://docs.google.com/spreadsheets/d/1v9xUqaSqgvDDlTpFqWtBXDPLKw6HsaFU5DfSO0d_9_0/edit
