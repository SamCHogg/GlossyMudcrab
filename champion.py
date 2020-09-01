from typing import List

import discord
from jinja2 import Template

import config
import cp
import exceptions


def help() -> discord.Embed:
    content = f"""
To use this command:
```{config.prefix}cp <Trial/Arena> (<Role>)```
{available_trials_template.render()}
{available_roles_template.render()}"""

    return discord.Embed(
        colour=discord.Color.red(),
        title="Champion Point Allocation",
        description=content
    )


async def handle_cp(message):
    split = message.content.split()
    length = len(split)
    embeds = []
    if length == 1 or length > 3:
        embeds = [help()]
    elif length == 2:
        embeds = create_embed_trial(split[1].lower())
    elif length == 3:
        embeds = create_embed_trial(split[1].lower(), split[2].lower())

    for embed in embeds:
        await message.channel.send(embed=embed)

    return


event_template = Template("""
**The Warrior**
{% for allocation in red -%}
{{ allocation.value }} {{ allocation.name }} 
{% endfor %}

**The Thief**
{% for allocation in green -%}
{{ allocation.value }} {{ allocation.name }} 
{% endfor -%}
""")

available_trials_template = Template("""
Available Trials/Arenas:
**AA** - Aetherian Archive
**AS** - Asylum Sanctorium
**BRP** - Blackrose Prison
**CR** - Cloudrest
**DSA** - Dragonstar Arena
**HoF** - Halls of Fabrication
**HRC** - Hel Ra Citadel
**KA** - Kyne's Aegis
**MA** - Maelstrom Arena
**MoL** - Maw of Lorkhaj
**SO** - Sanctum Ophidia
**SS** - Sunspire
""")

available_roles_template = Template("""
Available Roles:
**Tank** - Main Tank and Off Tank
**MT** - Main Tank
**OT** - Off Tank
**Healer** - Healer
**DPS** - Magicka and Stamina DPS
**MDPS** - Magicka DPS
**SDPS** - Stamina DPS
""")


def create_embed_trial(trial_str: str, role_str: str = None) -> List[discord.Embed]:
    try:
        trial = get_trial(trial_str)
    except exceptions.InvalidTrialName:
        embed = discord.Embed(
            colour=discord.Color.red(),
            title="Invalid Trial/Arena Name",
            description=available_trials_template.render()
        )
        return [embed]

    if role_str is not None:
        try:
            roles = get_roles(role_str)
        except exceptions.InvalidRoleName:
            embed = discord.Embed(
                colour=discord.Color.red(),
                title="Invalid Role Name",
                description=available_roles_template.render()
            )
            return [embed]
    else:
        roles = ["mt", "ot", "healer", "magicka", "stamina"]

    roles_cp = []
    for role in roles:
        try:
            roles_cp.append(cp.allocations["trial"][trial][role])
        except KeyError:
            pass

    if len(roles_cp) == 0:
        embed = discord.Embed(
            colour=discord.Color.red(),
            title="Invalid Options",
            description="There is no available CP allocation for this Trial/Arena and Role combination."
        )
        return [embed]

    embeds = []
    for role_cp in roles_cp:
        for setup in role_cp:
            embed = discord.Embed(
                colour=discord.Color.red(),
                title=setup["title"],
                description=event_template.render(red=setup["red"], green=setup["green"]),
                url="https://eso-u.com/champion-points"
            )
            embed.set_footer(text="ESO-U.com • Greymoor/Update 26")
            embeds.append(embed)
    return embeds


def get_trial(trial: str) -> str:
    if trial in {"aa", "naa", "vaa"}:
        return "aa"
    elif trial in {"as", "nas", "vas"}:
        return "as"
    elif trial in {"brp", "nbrp", "vbrp"}:
        return "brp"
    elif trial in {"cloudrest", "cr", "ncr", "vcr"}:
        return "cr"
    elif trial in {"dsa", "ndsa", "vdsa"}:
        return "dsa"
    elif trial in {"hof", "nhof", "vhof"}:
        return "hof"
    elif trial in {"hrc", "nhrc", "vhrc"}:
        return "hrc"
    elif trial in {"ka", "nka", "vka"}:
        return "ka"
    elif trial in {"ma", "nma", "vma"}:
        return "ma"
    elif trial in {"mol", "nmol", "vmol"}:
        return "mol"
    elif trial in {"so", "nso", "vso"}:
        return "so"
    elif trial in {"sunspire", "ss", "nss", "vss"}:
        return "ss"
    else:
        raise exceptions.InvalidTrialName()


def get_roles(role: str) -> List[str]:
    if role in {"tank"}:
        return ["mt", "ot"]
    elif role in {"mt"}:
        return ["mt"]
    elif role in {"ot"}:
        return ["ot"]
    elif role in {"healer"}:
        return ["healer"]
    elif role in {"dps"}:
        return ["magicka", "stamina"]
    elif role in {"magicka", "mdps", "mag"}:
        return ["magicka"]
    elif role in {"stamina", "sdps", "stam"}:
        return ["stamina"]
    else:
        raise exceptions.InvalidRoleName()
