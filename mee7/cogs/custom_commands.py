import asyncio
from typing import Dict, Callable

from discord.ext import commands


def period_to_seconds(period, number):
    if period in ['sec', 'second', 'seconds']:
        return number
    if period in ['min', 'minute', 'minutes']:
        return number * 60
    if period in ['hour', 'hours']:
        return number * 60 * 60

    return None


async def invalid_type(ctx):
    await ctx.send("I don't support that type of commands")


def process_cooldown(cooldown: str):
    """
    cooldown should be in the form of:
    int seconds/minutes/days
    """
    cooldown = cooldown.split()
    if len(cooldown) > 2:
        return None

    try:
        number = int(cooldown[0])
        if number <= 0:
            raise ValueError
    except ValueError:
        return None

    time_period = cooldown[1].lower()
    if time_period not in ['sec', 'second', 'seconds', 'min', 'minute', 'minutes', 'hour', 'hours']:
        return None

    return period_to_seconds(time_period, number)


class CustomCommands(commands.Cog, name="Custom Commands"):
    def __init__(self, bot):
        self.bot = bot

        self.types: Dict[str, Callable] = {
            'text': self.add_text_command,
        }

    @commands.command(brief='Add a custom command')
    @commands.has_permissions(administrator=True)
    async def add_command(self, ctx, type_):
        """add [type]"""
        await (self.types.get(type_.lower(), invalid_type))(ctx)

    async def exists(self, guild_id, name):
        for command in self.bot.walk_commands():
            if command.name == name or name in command.aliases:
                return True, False  # Exists and is not custom
        cmd = await self.bot.pg_con.fetchval(
            """
            SELECT cmd_name
              FROM commands
             WHERE g_id = $1
               AND cmd_name = $2
            """, guild_id, name
        )
        if cmd is None:
            return False
        else:
            return True, True  # Exists and is custom

    async def get_basic_command_info(self, ctx):
        def check(msg):
            return msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id

        try:
            await ctx.send("What will the __command name__ be? (case sensitive)")
            name = (await self.bot.wait_for('message', timeout=30.0, check=check)).content

            if exists_ := (await self.exists(ctx.guild.id, name)):
                await ctx.send(f"This command already exists. {'Maybe you want to edit it?' if exists_[1] else ''}")
                return

            await ctx.send("Do you want to set a __description__ for this command? [y/n]")
            yes_no = (await self.bot.wait_for('message', timeout=30.0, check=check)).content.lower()
            if yes_no in ['yes', 'y']:
                await ctx.send("Write the description")
                description = (await self.bot.wait_for('message', timeout=30.0, check=check)).content
            else:
                description = None

            await ctx.send("Do you want to set a __cooldown__ for this command? [y/n]")
            yes_no = (await self.bot.wait_for('message', timeout=30.0, check=check)).content.lower()
            if yes_no in ['yes', 'y']:
                await ctx.send("What is the cooldown per user? [number seconds/minutes/hours]")
                cooldown = (await self.bot.wait_for('message', timeout=30.0, check=check)).content

                # Get cooldown in seconds
                cooldown = process_cooldown(cooldown)
                if cooldown is None:
                    txt = f"Invalid input `{cooldown}`. There will be no cooldown for now but you can edit it later"
                    await ctx.send(txt)
            else:
                cooldown = None

            # TODO get allowed/banned roles and banned channels

            return name, description, cooldown

        except asyncio.TimeoutError:
            await ctx.send("You didn't reply fast enough, sorry, you will have to do it again")
            return None, None, None

    async def add_text_command(self, ctx):
        def check(msg):
            return msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id

        try:
            name, description, cooldown = await self.get_basic_command_info(ctx)

            if name is None:
                # Something went wrong, probably TimeoutError
                return

            await ctx.send("Will the bot __reply in dms__ or in the same channel? [dms/channel]")
            reply_in_dms = (await self.bot.wait_for('message', timeout=30.0, check=check)).content.lower() == "dms"

            await ctx.send("What will the bot reply with?")
            reply_with = (await self.bot.wait_for('message', timeout=120.0, check=check)).content

            await self.bot.pg_con.execute(
                """
                INSERT INTO commands (g_id, cmd_name, cmd_type, description, cooldown, reply_in_dms, reply_with)
                     VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, ctx.guild.id, name, 'text', description, cooldown, reply_in_dms, reply_with
            )

            await ctx.send(f"I added `{name}` as a command for your server")

        except asyncio.TimeoutError:
            await ctx.send("You didn't reply fast enough, sorry, you will have to do it again")


def setup(bot):
    bot.add_cog(CustomCommands(bot))
