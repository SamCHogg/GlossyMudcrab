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
    icon: str

    @classmethod
    def new(cls, id, name, mention, icon):
        return cls(
            id=id,
            name=name,
            mention=mention,
            icon=icon
        )

    @classmethod
    def from_discord_member(cls, discord_member: discord.Member, icon: str):
        return cls(
            id=discord_member.id,
            name=discord_member.name,
            mention=discord_member.mention,
            icon=icon,
        )


@dataclass
class MemberList(object):
    members: List[Member]
    limit: int
    default_icon: str

    @classmethod
    def new(cls, limit: int, default_icon: str):
        return cls(
            members=[],
            limit=limit,
            default_icon=default_icon
        )

    def is_full(self) -> bool:
        return len(self.members) >= self.limit

    # Check if a member is in the list
    def contains(self, member: Member) -> (bool, str):
        for signed_up in self.members:
            if member.id == signed_up.id:
                return True, signed_up.icon
        return False, ""

    # Check if a member is in the list and has the same icon
    def exactly_contains(self, member: Member) -> (bool, str):
        for signed_up in self.members:
            if member.id == signed_up.id and member.icon == signed_up.icon:
                return True, signed_up.icon
        return False, ""

    def to_list(self, fill_empty=True) -> List[Member]:
        member_list = []
        for i in range(self.limit):
            try:
                member_list.append(self.members[i])
            except IndexError:
                if fill_empty:
                    member_list.append(Member.new("", "", "", self.default_icon))
                else:
                    break
        return member_list

    def is_empty(self) -> bool:
        return len(self.members) == 0


@dataclass
class DPSMemberList(MemberList):
    stam_limit: int = -1
    mag_limit: int = -1

    @classmethod
    def new_with_separate_limits(cls, default_icon: str, stam_limit: int, mag_limit: int):
        return cls(
            members=[],
            limit=stam_limit+mag_limit,
            default_icon=default_icon,
            stam_limit=stam_limit,
            mag_limit=mag_limit,
        )


roster_template = Template("""
{% for member in roster -%}
    {{ member.icon }}: {{ member.mention }}
{% endfor -%}
""")

roster_template_numbered = Template("""
{% for member in roster -%}
    **{{loop.index}}.** {{ member.icon }}: {{ member.mention }}
{% endfor -%}
""")


@dataclass
class Roster(object):
    tanks: MemberList
    healers: MemberList
    dps: MemberList

    @classmethod
    def new(cls, tanks: int, healers: int, dps: int):
        return cls(
            tanks=MemberList.new(tanks, emojis.tank),
            healers=MemberList.new(healers, emojis.healer),
            dps=DPSMemberList.new(dps, f"{emojis.dps}"),
        )

    def to_list(self, fill_empty=True) -> List[Member]:
        return \
            self.tanks.to_list(fill_empty=fill_empty) + \
            self.healers.to_list(fill_empty=fill_empty) + \
            self.dps.to_list(fill_empty=fill_empty)

    def render(self, numbered=False, fill_empty=True):
        if numbered:
            template = roster_template_numbered
        else:
            template = roster_template
        return template.render(roster=self.to_list(fill_empty=fill_empty))

    def contains_member(self, member: Member) -> (bool, str):
        contains, icon = self.tanks.contains(member)
        if contains:
            return contains, icon

        contains, icon = self.healers.contains(member)
        if contains:
            return contains, icon

        contains, icon = self.dps.contains(member)
        if contains:
            return contains, icon

        return False, ""

    def is_empty(self) -> bool:
        return self.tanks.is_empty() and self.healers.is_empty() and self.dps.is_empty()
