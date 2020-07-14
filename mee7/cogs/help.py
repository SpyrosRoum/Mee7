import time
import asyncio

import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def n_embed(self, ctx, page: int, pages, cogs, cogs_dict):
        # TODO: Fix ugly embeds
        # TODO Add custom commands
        embed = discord.Embed(
            description=f"Prefix: `{ctx.prefix}`\n`[argument]` = required, `(argument)` = optional",
            color=ctx.author.color,
            timestamp=ctx.message.created_at
        )

        cog_name = cogs[page].replace("_", " ")
        embed.set_author(
            name=f"Help - {cog_name} - {len(cogs_dict[cogs[page]])} command(s)",
            icon_url=self.bot.user.avatar_url
        )
        embed.set_footer(text=f"Page {page+1}/{pages}")

        for command in cogs_dict[cogs[page]]:
            aliases = "None" if not command.aliases else [f"`{al}`" for al in command.aliases]

            val = (f"`{ctx.prefix}{command.help}`\n"
                   f"{command.brief}"
                   f"\nAliases: {'None' if aliases == 'None' else ', '.join(aliases)}")
            embed.add_field(name=command.name, value=val)

        return embed

    @commands.command(name="help", aliases=["h"], brief="Display this message", hidden=True)
    async def _help(self, ctx, *, command=None):
        '''help (command)'''
        if not command:
            commands_ = []
            for _command in self.bot.commands:
                if bool(_command.cog_name) and not _command.hidden:
                    try:
                        can_run = await _command.can_run(ctx)
                    except Exception:
                        can_run = False
                    if can_run:
                        commands_.append(_command)

            cogs = list(set(command.cog_name for command in commands_))

            cogs_dict = {}
            for cog in cogs:
                cogs_dict[cog] = []
                for _command in commands_:
                    if command.cog_name == cog:
                        cogs_dict[cog].append(_command)

            pages = len(cogs_dict)
            page = 0

            if not cogs:
                await ctx.send("It looks like you don't have permissions to run any command")
                return
            embed = self.n_embed(ctx, page, pages, cogs, cogs_dict)
            msg = await ctx.send(embed=embed)

            await msg.add_reaction('⬅')
            await msg.add_reaction('➡')
            await msg.add_reaction('❌')

            def check(r, _user):
                return _user != self.bot.user and r.message.id == msg.id

            t_end = time.time() + 300
            while time.time() < t_end:
                try:
                    res, user = await self.bot.wait_for('reaction_add', check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    continue

                if str(res.emoji) == "➡":
                    try:
                        await msg.remove_reaction('➡', user)
                    except discord.Forbidden:
                        pass
                    page += 1

                    if page == pages:
                        page -= 1

                    new_embed = self.n_embed(ctx, page, pages, cogs, cogs_dict)
                    await msg.edit(embed=new_embed)

                elif str(res.emoji) == "⬅":
                    try:
                        await msg.remove_reaction('⬅', user)
                    except discord.Forbidden:
                        pass

                    page -= 1
                    if page < 0:
                        page = 0

                    new_embed = self.n_embed(ctx, page, pages, cogs, cogs_dict)
                    await msg.edit(embed=new_embed)

                elif str(res.emoji) == "❌":
                    try:
                        await msg.remove_reaction("❌", user)
                    except discord.Forbidden:
                        pass

                    break

            await msg.remove_reaction('⬅', self.bot.user)
            await msg.remove_reaction('➡', self.bot.user)
            await msg.remove_reaction("❌", self.bot.user)
            await msg.edit(content=f"Type `{ctx.prefix}help` or `{ctx.prefix}h`", embed=None)
        else:
            command = self.bot.get_command(command)

            if not command:
                await ctx.send(f"Use the right command, try `{ctx.prefix}help`")
                return

            sub_commands = []
            if isinstance(command, commands.Group):
                sub_commands = list(command.commands)

            embed = discord.Embed(
                description=f"Prefix: `{ctx.prefix}`\n`[argument]` = required, `(argument)` = optional",
                color=ctx.author.color,
                timestamp=ctx.message.created_at
            )

            aliases = "None" if not command.aliases else [f"`{al}`" for al in command.aliases]
            txt = (f"`{ctx.prefix}{command.help}`"
                   f"\n{command.brief}"
                   f"\nAliases: {'None' if aliases == 'None' else ', '.join(aliases)}")
            embed.add_field(
                name=command.name,
                value=txt
            )

            for _command in sub_commands:
                txt = (f"`{ctx.prefix}{_command.help}`"
                       f"\n{_command.brief}"
                       f"\nAliases: {'None' if aliases == 'None' else ', '.join(aliases)}")
                embed.add_field(
                    name=f"**{_command.name}**",
                    value=txt,
                    inline=False
                )

            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
