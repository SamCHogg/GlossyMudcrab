# Glossy Mudcrab

A Discord bot to help organise Trials and Dungeon runs in ESO.

## Requirements

* [A Discord API Key](https://discordpy.readthedocs.io/en/latest/discord.html)
* A MongoDB Database - You can get one for free here https://www.mongodb.com/cloud/atlas
* [Pipenv](https://pypi.org/project/pipenv/)

## Setup

1. Make a copy of `example_config.py` called `config.py`. Place in here the connection information for MongoDB and the Discord API key.
2. Run using `pipenv run python main.py`

You'll likely want to use something like `screen` so that the application doesn't exit when you close the terminal.
