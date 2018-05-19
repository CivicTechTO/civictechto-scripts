# CivicTechTO Scripts

Helper scripts for CivicTechTO wrapped in a simple CLI.

We use this as a catch-all for simple scripts that help with organizing
tasks.

## Technologies Used

- **Python.** A programming langauge common in scripting.
- [**Click.**][click] A Python library for writing simple command-line
  tools.
- [**CircleCI.**][circleci] A continuous integration tool that we use
  run scheduled scripts in the cloud.

## Setup

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

<!-- Links -->
   [click]: http://click.pocoo.org/5/
   [circleci]: https://circleci.com/docs/2.0/about-circleci/
