import os
import sys

import discord

import emojis
import event
import event_setup
import reactions
import roster

# Config.py setup
##################################################################################
if not os.path.isfile("config.py"):
    sys.exit("'config.py' not found! Please add it and try again.")

else:
    import config  # config.py is required to run; found in the same directory.
##################################################################################

client = discord.Client()


async def help_command(message):
    help_message = f"""Hello \N{WAVING HAND SIGN}
    
You can create a new trial event with **{config.prefix}trial**, I will message you to ask more questions about the event.
    """
    await message.channel.send(content=help_message)
    await message.delete()


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name=f'{config.prefix}mudcrab'))
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.startswith(config.prefix):
        return

    command = message.content[1:]
    if command.startswith('trial'):
        await event_setup.interactive_setup(client, message)
    elif command.startswith('mudcrab'):
        await help_command(message)


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    user = client.get_user(payload.user_id)
    # Ignore reactions from the client
    if user is None or user == client.user:
        return

    # Get the message from the IDs
    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    # Ignore reactions to other messages
    if message.author != client.user:
        return

    if payload.emoji.name == emojis.tank:
        await add_role(message, user, payload.emoji.name, event.add_tank)
    elif payload.emoji.name == emojis.healer:
        await add_role(message, user, payload.emoji.name, event.add_healer)
    elif payload.emoji.name == emojis.stam_dps:
        await add_role(message, user, payload.emoji.name, event.add_dps)
    elif payload.emoji.name == emojis.mag_dps:
        await add_role(message, user, payload.emoji.name, event.add_dps)
    elif payload.emoji.name == emojis.edit:
        await reactions.remove_reaction(message, user, payload.emoji)
        await event_setup.edit_event(client, message, user)
    else:
        await message.remove_reaction(payload.emoji, user)


@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    user = client.get_user(payload.user_id)
    if user is None or user == client.user:
        return

    # Get the message from the IDs
    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    # Ignore reactions to other messages
    if message.author != client.user:
        return

    if payload.emoji.name == emojis.tank:
        await remove_role(message, user, payload.emoji.name, event.remove_tank)
    elif payload.emoji.name == emojis.healer:
        await remove_role(message, user, payload.emoji.name, event.remove_healer)
    elif payload.emoji.name == emojis.stam_dps:
        await remove_role(message, user, payload.emoji.name, event.remove_dps)
    elif payload.emoji.name == emojis.mag_dps:
        await remove_role(message, user, payload.emoji.name, event.remove_dps)


async def add_role(message, user, emoji, add_func):
    this_event = event.Event.from_db(message.id)
    try:
        this_event = add_func(this_event, roster.Member.from_discord_member(user, emoji))
    except event.RosterFullException:
        await reactions.remove_reaction(message, user, emoji)
        await message.channel.send(f"We don't need anymore {emoji} {user.mention}")
    except event.AlreadySignedUpException as e:
        # If the existing role is the same we just continue
        if e.role != emoji:
            await reactions.remove_reaction(message, user, emoji)
            await message.channel.send(f"{user.mention} you are already signed up as {e.role}")
    except event.EventNotFoundException:
        await reactions.remove_reaction(message, user, emoji)
        await message.channel.send(f"{user.mention} I was unable to add you as {emoji}")
    else:
        await message.edit(content=this_event.render())
        await message.channel.send(f"{user.name} joined as {emoji}")


async def remove_role(message, user, emoji, remove_fun):
    this_event = event.Event.from_db(message.id)
    this_event, changed = remove_fun(this_event, roster.Member.from_discord_member(user, emoji))
    if changed:
        await message.edit(content=this_event.render())
        await message.channel.send(f"{user.name} has signed off as {emoji}")


if __name__ == "__main__":
    client.run(config.token)
