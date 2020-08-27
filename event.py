from datetime import datetime

import config
from dacite import from_dict
from dataclasses import dataclass, asdict

import emojis
import roster as event_roster
from pymongo import MongoClient
from jinja2 import Template

event_template = Template("""
{{ event.name }} scheduled for {{ event.when }}

{{ emojis.crown }}{{ event.creator.mention }}{{ emojis.crown }}

{{ event.description }}

**Roster:**
{{ event.roster.render() }}

**React with:**
{{ emojis.tank }} to sign in as Tank
{{ emojis.healer }} to sign in as Healer
{{ emojis.dps }} to sign in as Damage Dealer
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


class AlreadySignedUpException(Exception):
    role: str

    def __init__(self, message, role):
        self.role = role
        super().__init__(message)


class RosterFullException(Exception):
    pass


class EventNotFoundException(Exception):
    pass


def add_tank(event: Event, member: event_roster.Member) -> object:
    if len(event.roster.tanks) >= event.roster.tank_limit:
        raise RosterFullException("")

    contains, role = event.roster.contains_member(member)
    if contains:
        raise AlreadySignedUpException("", role)

    result = collection.update_one(
        {"_id": event._id},
        {"$push": {"roster.tanks": asdict(member)}}
    )

    if result.modified_count != 1:
        raise EventNotFoundException("")

    return event.from_db(_id=event._id)


def add_healer(event: Event, member: event_roster.Member) -> object:
    if len(event.roster.healers) >= event.roster.healer_limit:
        raise RosterFullException("")

    contains, role = event.roster.contains_member(member)
    if contains:
        raise AlreadySignedUpException("", role)

    result = collection.update_one(
        {"_id": event._id},
        {"$push": {"roster.healers": asdict(member)}}
    )

    if result.modified_count != 1:
        raise EventNotFoundException("")

    return event.from_db(_id=event._id)


def add_dps(event: Event, member: event_roster.Member) -> object:
    if len(event.roster.dps) >= event.roster.dps_limit:
        raise RosterFullException("")

    contains, role = event.roster.contains_member(member)
    if contains:
        raise AlreadySignedUpException("", role)

    result = collection.update_one(
        {"_id": event._id},
        {"$push": {"roster.dps": asdict(member)}}
    )
    if result.modified_count != 1:
        raise EventNotFoundException("")

    return event.from_db(_id=event._id)


def remove_tank(event: Event, member: event_roster.Member) -> (object, bool):
    for tank in event.roster.tanks:
        if member == tank:
            result = collection.update_one(
                {"_id": event._id},
                {"$pull": {"roster.tanks": {"id": member.id}}}
            )
            if result.modified_count != 1:
                raise EventNotFoundException("")

            return event.from_db(_id=event._id), True

    return event, False


def remove_healer(event: Event, member: event_roster.Member) -> (object, bool):
    for healer in event.roster.healers:
        if member == healer:
            result = collection.update_one(
                {"_id": event._id},
                {"$pull": {"roster.healers": {"id": member.id}}}
            )
            if result.modified_count != 1:
                raise EventNotFoundException("")

            return event.from_db(_id=event._id), True

    return event, False


def remove_dps(event: Event, member: event_roster.Member) -> (object, bool):
    for dps in event.roster.dps:
        if member == dps:
            result = collection.update_one(
                {"_id": event._id},
                {"$pull": {"roster.dps": {"id": member.id}}}
            )
            if result.modified_count != 1:
                raise EventNotFoundException("")

            return event.from_db(_id=event._id), True

    return event, False
