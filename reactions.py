import discord


async def remove_reaction(message, user, emoji):
    try:
        await message.remove_reaction(emoji, user)
    except (discord.Forbidden, discord.NotFound):
        # Maybe send a message?
        pass
