from jinja2 import Template
import discord
from dataclasses import dataclass

from typing import List

import emojis


@dataclass
class Member(object):
    id: int
    name: str
    mention: str

    @classmethod
    def new(cls, id, name, mention):
        return cls(
            id=id,
            name=name,
            mention=mention
        )

    @classmethod
    def from_discord_member(cls, discord_member: discord.Member):
        return cls(
            id=discord_member.id,
            name=discord_member.name,
            mention=discord_member.mention
        )

    def __eq__(self, other):
        if isinstance(other, Member):
            return self.id == other.id
        return False


roster_template = Template("""
{% for i in range(roster.tank_limit) -%}
    {{ emojis.tank }}: {% if roster.tanks[i] %}{{ roster.tanks[i].mention }}{% endif %}
{% endfor -%}
{% for i in range(roster.healer_limit) -%}
     {{ emojis.healer }}: {% if roster.healers[i] %}{{ roster.healers[i].mention }}{% endif %}
{% endfor -%}
{% for i in range(roster.dps_limit) -%}
    {{ emojis.dps }}: {% if roster.dps[i] %}{{ roster.dps[i].mention }}{% endif %}
{% endfor -%}
""")


@dataclass
class Roster(dict):
    tanks: List[Member]
    tank_limit: int
    healers: List[Member]
    healer_limit: int
    dps: List[Member]
    dps_limit: int

    @classmethod
    def new(cls, tanks: int, healers: int, dps: int):
        return cls(
            tanks=[],
            tank_limit=tanks,
            healers=[],
            healer_limit=healers,
            dps=[],
            dps_limit=dps
        )

    def render(self):
        return roster_template.render(roster=self, emojis=emojis.emojis)

    def contains_member(self, member) -> (bool, str):
        for tank in self.tanks:
            if member == tank:
                return True, emojis.tank

        for healer in self.healers:
            if member == healer:
                return True, emojis.healer

        for dps in self.dps:
            if member == dps:
                return True, emojis.dps

        return False, ""
