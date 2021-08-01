import os

# Discord Bot token here
token = os.environ.get('GLOSSY_DISCORD_TOKEN')
# Prefix for commands
prefix = '!'
# MongoDB address including any credentials
db_address = os.environ.get('GLOSSY_DB_ADDRESS')
# Name of the MongoDB database
db_name = 'ESOBot'
