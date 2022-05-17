# readers_diary_bot
Simple Python bot for reader. You can save your reviews to all book you've read in here

# Dependencies
python-telegram-bot>=20.0a0

# Set up
## Prepare virtual environment
```sh
$ python3 -m venv .venv
$ source .venv/bin/activate
(.venv)$ pip install 'python-telegram-bot>=20.0a0'
```

## Set up env data
Bot have to connect to Telegram and save your data somewhere. That's why it needs to get BOT_TOKEN and BOT_DB from you.
One of the simplest way for it to get this information is to put it in .env file. Usually it is quite simple:
```sh
export BOT_TOKEN=<token>
export BOT_DB=<path_to_sqlite3_db_file>
```
Now run this command to set up the environment:
```sh
(.venv) $ source .env
```
## Run bot
```sh
(.venv) $ python main.py
```

# What can bot do?
## Authors
* /add_author <AUTHOR_NAME> - add author
* /list_authors - list all your authors
* /remove_author - remove an author
## Stories
* /add_story <STORY_TITLE> - add story
* /list_stories - list all your stories
* /remove_story - remove an story
## Reviews
* /add_review <REVIEW_TEXT> - add review
* /list_reviews - list all your reviews
* /remove_review - remove an review
