import discord
from jinja2 import Template

import config
import trial_cp
import build_cp

available_trials_template = Template("""
**Trial and Arena Options:**
{% for trial in trials -%}
{{ trial.names.0 }}{{ ", " if not loop.last }}
{%- endfor -%}
""")

available_builds_template = Template("""
**Build Options:**
{% for build in builds -%}
{{ build.names.0 }}{{ ", " if not loop.last }}
{%- endfor -%}
""")


def help() -> discord.Embed:
    trials = available_trials_template.render(trials=trial_cp.trials)
    builds = available_builds_template.render(builds=build_cp.builds)

    content = f"""
**Using the command**
To show CP allocations for a Trial, Arena or Build use one of the below options:
```{config.prefix}cp <option>```
{trials}
{builds}
"""
    return discord.Embed(
        colour=discord.Color.red(),
        title="Champion Point Allocation",
        description=content
    )


async def handle_cp(message):
    split = message.content.split()
    length = len(split)
    if length == 1:
        embed = help()
    else:
        embed = create_trial_or_build_embed("".join(split[1:]))
    await message.channel.send(embed=embed)


def create_trial_or_build_embed(s: str) -> discord.Embed:
    trial, exists = get_trial(s)
    if exists:
        return create_embed_trial(trial)

    build, exists = get_build(s)
    if exists:
        return create_embed_build(build)

    return help()


def get_trial(s: str) -> (dict, bool):
    for trial in trial_cp.trials:
        for name in trial["names"]:
            if name.lower() == s.lower():
                return trial, True
    return None, False


def get_build(s: str) -> (dict, bool):
    for build in build_cp.builds:
        for name in build["names"]:
            if name.lower() == s.lower():
                return build, True
    return None, False


trial_role_cp_template = Template("""
{% for role in roles %}
**{{ role.name }}**
{% for allocation in role.red -%}
{{ allocation.value }} {{ allocation.name }}{{ ", " if not loop.last }}
{%- endfor %}
    
{% for allocation in role.green -%}
{{ allocation.value }} {{ allocation.name }}{{ ", " if not loop.last }}
{%- endfor %}
{% endfor %}
""")


def create_embed_trial(trial: dict) -> discord.Embed:
    message = trial_role_cp_template.render(roles=trial["roles"])
    return create_cp_embed(discord.Color.red(), trial["display_name"], message)


build_cp_template = Template("""
{% for build in builds %}
**{{ build.name }}**
{% for allocation in build.blue -%}
{{ allocation.value }} {{ allocation.name }}{{ ", " if not loop.last }}
{%- endfor %}
{% endfor %}
""")


def create_embed_build(build: dict) -> discord.Embed:
    message = build_cp_template.render(builds=build["builds"])
    return create_cp_embed(discord.Color.blue(), build["display_name"], message)


def create_cp_embed(colour, title, message) -> discord.Embed:
    embed = discord.Embed(
        colour=colour,
        title=title,
        description=message,
        url="https://eso-u.com/champion-points"
    )
    embed.set_footer(text="ESO-U.com • Stonethorn/Update 27")
    return embed
