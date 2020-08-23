import asyncio
import discord

import emojis
import roster
import event


class Field(object):
    name = "Override"
    text = "Override"

    async def __wait_for_response(self, client, dm):
        def check(m):
            return m.author != client.user and m.channel.id == dm.id

        try:
            msg = await client.wait_for('message', timeout=60, check=check)
        except asyncio.exceptions.TimeoutError:
            await dm.send("Waited too long for response.")
            return "", True
        if msg.content == "cancel":
            await dm.send("Okay! Setup canceled.")
            return "", True
        return msg, False

    async def input(self, client, dm):
        message = self.text
        validates = False
        response = None
        while not validates:
            await dm.send(message)
            response, canceled = await self.__wait_for_response(client, dm)
            if canceled:
                return None
            validates, message = self.validate(response)

        return self.handler(response)

    def validate(self, msg):
        return True, ""

    def handler(self, msg):
        return msg.content


class NameField(Field):
    name = "Name"
    short_text = "Enter the **name** for this event (50 character limit):"
    text = f"**Event setup**\nYou can type *cancel* at any point during this process to cancel the event creation.\n\n{short_text} "

    def validate(self, msg):
        if len(msg.content) > 50:
            return False, f"Invalid input, the name must be less than 50 characters.\n{self.short_text}"
        return True, ""


class DescriptionField(Field):
    name = "Description"
    text = "Enter this event's **description**:"


class WhenField(Field):
    name = "When"
    text = "Enter the **time** and **date** for this event:"


class RosterField(Field):
    name = "Roster"
    text = """Select a roster setup:
**1.** 1 Tank, 2 Healer, 9 DPS
**2.** 2 Tank, 2 Healer, 8 DPS
**3.** 3 Tank, 2 Healer, 7 DPS
**0.** Custom"""

    def validate(self, msg):
        if not msg.content.isnumeric():
            return False, f"Invalid input, you must choose a number.\n{self.text}"
        choice = int(msg.content)
        if choice == 0:
            return False, f"Sorry this is not yet implemented. Choose one of the existing choices!\n{self.text}"
        if choice < 1 or choice > 3:
            return False, f"Invalid input, you must choose one of the following.\n{self.text}"
        return True, ""

    def handler(self, msg):
        choice = int(msg.content)
        if choice == 1:
            return roster.Roster.new(tanks=1, healers=2, dps=9)
        elif choice == 2:
            return roster.Roster.new(tanks=2, healers=2, dps=8)
        elif choice == 3:
            return roster.Roster.new(tanks=3, healers=2, dps=7)
        return None


async def interactive_setup(client, message):
    original = message.channel
    dm = message.author.dm_channel
    if dm is None:
        dm = await message.author.create_dm()

    # Delete the command message
    try:
        await message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass

    name = await NameField().input(client, dm)
    if name is None:
        return

    description = await DescriptionField().input(client, dm)
    if description is None:
        return

    when = await WhenField().input(client, dm)
    if when is None:
        return

    emptyRoster = await RosterField().input(client, dm)
    if roster is None:
        return

    creator = roster.Member.from_discord_member(message.author)

    newEvent = event.Event.new(name, description, when, emptyRoster, creator)

    eventMessage = await original.send(newEvent.render())
    newEvent.save(eventMessage.id)

    await eventMessage.add_reaction(emojis.tank)
    await eventMessage.add_reaction(emojis.healer)
    await eventMessage.add_reaction(emojis.dps)
    await eventMessage.add_reaction(emojis.edit)

    await dm.send(f"Event '{name}' created in {original.mention}")
