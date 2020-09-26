import asyncio
import discord

import emojis
import reactions
import roster
import event

# How long to wait for a response before timing out
message_timeout = 300


class Field(object):
    name = "NOT IMPLEMENTED"
    text = "NOT IMPLEMENTED"

    async def __wait_for_response(self, client, dm):
        def check(m):
            return m.author != client.user and m.channel.id == dm.id

        try:
            msg = await client.wait_for('message', timeout=message_timeout, check=check)
        except asyncio.exceptions.TimeoutError:
            await dm.send("Waited too long for response.")
            return "", True
        if msg.content.lower() == "cancel":
            await dm.send("Okay \N{CRYING FACE}")
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
    text = "Enter the **name** for this event:"

    def validate(self, msg):
        if len(msg.content) > 30:
            return False, f"Invalid input, the name must be less than 30 characters.\n{self.text}"
        return True, ""


class IntroField(NameField):
    short_text = "Enter the **name** for this event:"
    text = f"**Event setup**\nYou can type *cancel* at any point during this process to cancel the event creation.\n\n{short_text} "

    def validate(self, msg):
        if len(msg.content) > 30:
            return False, f"Invalid input, the name must be less than 30 characters.\n{self.short_text}"
        return True, ""


class DescriptionField(Field):
    name = "Description"
    text = "Enter a **description** for this event:"

    def validate(self, msg):
        if len(msg.content) > 200:
            return False, f"Invalid input, the description must be less than 200 characters.\n{self.text}"
        return True, ""


class WhenField(Field):
    name = "When"
    text = "Enter the **time** and **date** for this event:"

    def validate(self, msg):
        if len(msg.content) > 50:
            return False, f"Invalid input, must be less than 50 characters.\n{self.text}"
        return True, ""


class RosterField(Field):
    name = "Roster"
    text = """Select a roster setup:
**1.** 1 Tank, 2 Healer, 9 DPS
**2.** 2 Tank, 2 Healer, 8 DPS
**3.** 3 Tank, 2 Healer, 7 DPS
**4.** 1 Tank, 1 Healer, 2 DPS
**5.** 1 Tank, 3 DPS
**0.** Custom"""

    def validate(self, msg):
        if not msg.content.isnumeric():
            return False, f"Invalid input, you must choose a number.\n{self.text}"
        choice = int(msg.content)
        if choice == 0:
            return False, f"Sorry this is not yet implemented. Choose one of the existing choices!\n{self.text}"
        if choice < 1 or choice > 5:
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
        elif choice == 4:
            return roster.Roster.new(tanks=1, healers=1, dps=2)
        elif choice == 5:
            return roster.Roster.new(tanks=1, healers=0, dps=3)
        return None


class EditOptionsField(Field):
    name = "Edit"
    event_name = ""
    options = """Select a field to edit:
**1.** Name
**2.** Description
**3.** Time
**4.** Roster"""

    def __init__(self, event_name: str):
        self.event_name = event_name
        self.text = f"**Edit {event_name}**\nYou can type *cancel* at any point during this process to cancel the event creation.\n\n{self.options}"

    def validate(self, msg):
        if not msg.content.isnumeric():
            return False, f"Invalid input, you must choose a number.\n{self.options}"
        choice = int(msg.content)
        if choice < 1 or choice > 4:
            return False, f"Invalid input, you must choose one of the following.\n{self.options}"
        return True, ""

    def handler(self, msg):
        return int(msg.content)


class EditRosterField(Field):
    name = "EditRoster"
    this_event: event.Event
    text: str

    def __init__(self, this_event: event.Event):
        self.this_event = this_event
        self.text = f"Select someone to remove:\n{this_event.roster.render(numbered=True, fill_empty=False)}"

    def validate(self, msg):
        if not msg.content.isnumeric():
            return False, f"Invalid input, you must choose a number.\n{self.text}"
        choice = int(msg.content)
        if choice < 1 or choice > len(self.this_event.roster.to_list(fill_empty=False)):
            return False, f"Invalid input, you must choose one of the following.\n{self.text}"
        return True, ""

    def handler(self, msg):
        roster_list = self.this_event.roster.to_list(fill_empty=False)
        return roster_list[int(msg.content)-1]


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

    name = await IntroField().input(client, dm)
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

    creator = roster.Member.from_discord_member(message.author, emojis.crown)

    newEvent = event.Event.new(name, description, when, emptyRoster, creator)

    eventMessage = await original.send(newEvent.render())
    newEvent.save(eventMessage.id)

    await eventMessage.add_reaction(emojis.tank)
    await eventMessage.add_reaction(emojis.healer)
    await eventMessage.add_reaction(emojis.stam_dps)
    await eventMessage.add_reaction(emojis.mag_dps)
    await eventMessage.add_reaction(emojis.edit)
    await eventMessage.add_reaction(emojis.ping)

    await eventMessage.pin()

    await dm.send(f"Event '{name}' created in {original.mention}")


async def edit_event(client, message: discord.Message, user: discord.Member):
    this_event = event.Event.from_db(message.id)
    if not this_event.is_creator(user):
        return

    dm = user.dm_channel
    if dm is None:
        dm = await user.create_dm()

    choice = await EditOptionsField(this_event.name).input(client, dm)
    if choice is None:
        return

    # Change name
    if choice == 1:
        name = await NameField().input(client, dm)
        if name is None:
            return
        this_event = event.edit_name(this_event, name)
        await message.edit(content=this_event.render())

    # Change description
    elif choice == 2:
        desc = await DescriptionField().input(client, dm)
        if desc is None:
            return
        this_event = event.edit_description(this_event, desc)
        await message.edit(content=this_event.render())

    # Change date or time
    elif choice == 3:
        when = await WhenField().input(client, dm)
        if when is None:
            return
        this_event = event.edit_when(this_event, when)
        await message.edit(content=this_event.render())

    # Remove someone from the roster
    elif choice == 4:
        member = await EditRosterField(this_event).input(client, dm)
        if member is None:
            return
        this_event = event.remove_member(this_event, member)
        await reactions.remove_reaction(message, member, emojis.tank)
        await reactions.remove_reaction(message, member, emojis.healer)
        await reactions.remove_reaction(message, member, emojis.stam_dps)
        await reactions.remove_reaction(message, member, emojis.mag_dps)
        await message.edit(content=this_event.render())
        await message.channel.send(f"{member.name} has been removed from the roster by {this_event.creator.name}")
    else:
        return

    await dm.send(f"Event '{this_event.name}' has been edited")
