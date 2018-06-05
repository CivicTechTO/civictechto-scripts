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

This moves all Trello cards from the pitch list to the active column.
The idea is to schedule it to run prior to each hacknight.

```
python clean_pitch_list.py
```

### `update_pitch_csv.py`

This updates the [historical dataset of breakout
groups][breakout-dataset] who pitched each week.

### `notify_slack.py`

This drops a message in Slack announcing who pitched this week.

<!-- Links -->
   [click]: http://click.pocoo.org/5/
   [circleci]: https://circleci.com/docs/2.0/about-circleci/
   [circleci-cron]: https://support.circleci.com/hc/en-us/articles/115015481128-Scheduling-jobs-cron-for-builds-
   [circleci-proj]: https://circleci.com/gh/civictechto/civictechto-scripts
   [circleci-config]:.circleci/config.yml#L126
   [breakout-dataset]: https://github.com/CivicTechTO/dataset-civictechto-breakout-groups/blob/master/data/civictechto-breakout-groups.csv
