from datetime import datetime

import discord

import config
from dacite import from_dict
from dataclasses import dataclass, asdict

import emojis
import roster as event_roster
from pymongo import MongoClient
from jinja2 import Template

from exceptions import RosterFullException, AlreadySignedUpException, EventNotFoundException

event_template = Template("""
{{ event.name }} scheduled for {{ event.when }}

{{ emojis.crown }}{{ event.creator.mention }}{{ emojis.crown }}

{{ event.description }}

**Roster:**
{{ event.roster.render() }}

**React with:**
{{ emojis.tank }} to sign in as Tank
{{ emojis.healer }} to sign in as Healer
{{ emojis.stam_dps }} to sign in as Stamina DPS
{{ emojis.mag_dps }} to sign in as Magicka Dps
{{ emojis.edit }} To edit the trial ({{ emojis.crown }} only)
""")

cluster = MongoClient(config.db_address)
db = cluster[config.db_name]
collection = db["Events"]
# Setup automatic deletion of events
# Deleted after 1 month
collection.create_index("createdAt", expireAfterSeconds=1*60*60*24*30)


@dataclass
class Event(object):
    _id: int
    name: str
    description: str
    when: str
    roster: event_roster.Roster
    creator: event_roster.Member
    createdAt: datetime

    @classmethod
    def from_db(cls, _id):
        json_data = collection.find_one({"_id": _id})
        event = from_dict(data_class=cls, data=json_data)
        return event

    @classmethod
    def new(cls, name: str, description: str, when: str, roster: event_roster.Roster, creator: event_roster.Member):
        return cls(
            _id=0,
            name=name,
            description=description,
            when=when,
            roster=roster,
            creator=creator,
            createdAt=datetime.utcnow()
        )

    def render(self):
        return event_template.render(event=self, emojis=emojis.emojis)

    def save(self, _id):
        self._id = _id
        collection.insert_one(asdict(self))

    def is_creator(self, user: discord.User):
        return user.id == self.creator.id


def add_tank(event: Event, member: event_roster.Member) -> Event:
    if event.roster.tanks.is_full():
        raise RosterFullException("")

    contains, role = event.roster.contains_member(member)
    if contains:
        raise AlreadySignedUpException("", role)

    result = collection.update_one(
        {"_id": event._id},
        {"$push": {"roster.tanks.members": asdict(member)}}
    )

    if result.modified_count != 1:
        raise EventNotFoundException("")

    return event.from_db(_id=event._id)


def add_healer(event: Event, member: event_roster.Member) -> Event:
    if event.roster.healers.is_full():
        raise RosterFullException("")

    contains, role = event.roster.contains_member(member)
    if contains:
        raise AlreadySignedUpException("", role)

    result = collection.update_one(
        {"_id": event._id},
        {"$push": {"roster.healers.members": asdict(member)}}
    )

    if result.modified_count != 1:
        raise EventNotFoundException("")

    return event.from_db(_id=event._id)


def add_dps(event: Event, member: event_roster.Member) -> Event:
    if event.roster.dps.is_full():
        raise RosterFullException("")

    contains, role = event.roster.contains_member(member)
    if contains:
        raise AlreadySignedUpException("", role)

    result = collection.update_one(
        {"_id": event._id},
        {"$push": {"roster.dps.members": asdict(member)}}
    )
    if result.modified_count != 1:
        raise EventNotFoundException("")

    return event.from_db(_id=event._id)


def remove_tank(event: Event, member: event_roster.Member) -> (Event, bool):
    contains, icon = event.roster.tanks.exactly_contains(member)
    if contains:
        result = collection.update_one(
            {"_id": event._id},
            {"$pull": {"roster.tanks.members": {"id": member.id}}}
        )
        if result.modified_count != 1:
            return event, False

        return event.from_db(_id=event._id), True

    return event, False


def remove_healer(event: Event, member: event_roster.Member) -> (Event, bool):
    contains, icon = event.roster.healers.exactly_contains(member)
    if contains:
        result = collection.update_one(
            {"_id": event._id},
            {"$pull": {"roster.healers.members": {"id": member.id}}}
        )
        if result.modified_count != 1:
            return event, False

        return event.from_db(_id=event._id), True

    return event, False


def remove_dps(event: Event, member: event_roster.Member) -> (Event, bool):
    contains, icon = event.roster.dps.exactly_contains(member)
    if contains:
        result = collection.update_one(
            {"_id": event._id},
            {"$pull": {"roster.dps.members": {"id": member.id}}}
        )
        if result.modified_count != 1:
            return event, False

        return event.from_db(_id=event._id), True

    return event, False


def edit_name(event: Event, name: str) -> Event:
    result = collection.update_one(
        {"_id": event._id},
        {"$set": {"name": name}}
    )

    if result.modified_count != 1:
        raise EventNotFoundException("")

    return event.from_db(_id=event._id)


def edit_description(event: Event, description: str) -> Event:
    result = collection.update_one(
        {"_id": event._id},
        {"$set": {"description": description}}
    )

    if result.modified_count != 1:
        raise EventNotFoundException("")

    return event.from_db(_id=event._id)


def edit_when(event: Event, when: str) -> Event:
    result = collection.update_one(
        {"_id": event._id},
        {"$set": {"when": when}}
    )

    if result.modified_count != 1:
        raise EventNotFoundException("")

    return event.from_db(_id=event._id)

