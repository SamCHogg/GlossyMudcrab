import os
import sys

import discord

import emojis
import event
import event_setup
import roster

# Config.py setup
##################################################################################
if not os.path.isfile("config.py"):
    sys.exit("'config.py' not found! Please add it and try again.")

else:
    import config  # config.py is required to run; found in the same directory.
##################################################################################

client = discord.Client()


@client.event
async def on_ready():
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


@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.Member):
    if reaction.message.author != client.user:
        return

    if user == client.user:
        return

    if reaction.emoji == emojis.tank:
        await add_role(reaction, user, event.add_tank)
    elif reaction.emoji == emojis.healer:
        await add_role(reaction, user, event.add_healer)
    elif reaction.emoji == emojis.dps:
        await add_role(reaction, user, event.add_dps)
    else:
        await remove_reaction(reaction, user)


@client.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.Member):
    if reaction.message.author != client.user:
        return

    if user == client.user:
        return

    if reaction.emoji == emojis.tank:
        await remove_role(reaction, user, event.remove_tank)
    elif reaction.emoji == emojis.healer:
        await remove_role(reaction, user, event.remove_healer)
    elif reaction.emoji == emojis.dps:
        await remove_role(reaction, user, event.remove_dps)


async def add_role(reaction, user, add_func):
    this_event = event.Event.from_db(reaction.message.id)
    try:
        this_event = add_func(this_event, roster.Member.from_discord_member(user))
    except event.RosterFullException:
        await remove_reaction(reaction, user)
        await reaction.message.channel.send(f"We don't need anymore {reaction.emoji} {user.mention}")
    except event.AlreadySignedUpException as e:
        await remove_reaction(reaction, user)
        await reaction.message.channel.send(f"{user.mention} you are already signed up as {e.role}")
    else:
        await reaction.message.edit(content=this_event.render())
        await reaction.message.channel.send(f"{user.name} joined as {reaction.emoji}")


async def remove_role(reaction, user, remove_fun):
    this_event = event.Event.from_db(reaction.message.id)
    this_event, changed = remove_fun(this_event, roster.Member.from_discord_member(user))
    if changed:
        await reaction.message.edit(content=this_event.render())
        await reaction.message.channel.send(f"{user.name} has signed off as {reaction.emoji}")


async def remove_reaction(reaction, user):
    try:
        await reaction.remove(user)
    except (discord.Forbidden, discord.NotFound):
        # Maybe send a message?
        pass


if __name__ == "__main__":
    client.run(config.token)
