import asyncio

import discord
from discord.ext import commands

async def is_bot_owner(ctx):
    return await ctx.bot.is_owner(ctx.author)

class SetUp(commands.Cog, name="Set up"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(brief="Ask for the help of this command for more", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx):
        """welcome [sub command]"""
        pass

    @welcome.command(aliases=['chn'], brief='Set the channel for the welcome message')
    @commands.has_permissions(administrator=True)
    async def channel(self, ctx, channel: discord.TextChannel=None):
        """welcome channel (channel)"""
        if channel is None:
            await self.bot.pg_con.execute(
                """
                INSERT INTO settings (g_id, welcome_chn_id)
                     VALUES ($1, $2)
                ON CONFLICT (g_id)
                DO
                    UPDATE
                       SET welcome_chn_id = EXCLUDED.welcome_chn_id
                """, ctx.guild.id, None
            )

            await ctx.send("There will be no welcome channel")
        else:
            await self.bot.pg_con.execute(
                """
                INSERT INTO settings (g_id, welcome_chn_id)
                     VALUES ($1, $2)
                ON CONFLICT (g_id)
                DO
                    UPDATE
                       SET welcome_chn_id = EXCLUDED.welcome_chn_id
                """, ctx.guild.id, channel.id
            )

            await ctx.send(f"{channel.mention} will be used for the welcome message."
                        f"Use `{ctx.prefix}welcome message` for the message")

    @welcome.command(aliases=['msg'], brief='Set the welcome message')
    @commands.has_permissions(administrator=True)
    async def message(self, ctx, *, msg):
        """welcome message [message]"""
        await self.bot.pg_con.execute(
            """
                INSERT INTO settings (g_id, welcome_msg)
                     VALUES ($1, $2)
                ON CONFLICT (g_id)
                DO
                    UPDATE
                       SET welcome_msg = EXCLUDED.welcome_msg
                """, ctx.guild.id, msg
        )

        await ctx.send(f"`{msg}` will be sent when someone joins if you have set up the welcome channel.")

    @welcome.command(brief='Set the role for people who join, leave empty to de-activate it')
    @commands.has_permissions(administrator=True)
    async def role(self, ctx, role: discord.Role=None):
        """welcome role (role)"""
        await self.bot.pg_con.execute(
            """
                INSERT INTO settings (g_id, auto_role_id)
                     VALUES ($1, $2)
                ON CONFLICT (g_id)
                DO
                    UPDATE
                       SET auto_role_id = EXCLUDED.auto_role_id
                """, ctx.guild.id, role.id
        )

        if role is not None:
            await ctx.send(f"`{role.name}` will be given when someone joins.")

            self.bot.roles[ctx.guild.id] = role.id
        else:
            await ctx.send("There will be no role given to new members")

            self.bot.roles[ctx.guild.id] = None

    @commands.command(brief='Set the suggestions channel, leave empy to remove it')
    @commands.has_permissions(administrator=True)
    async def suggestions_chn(self, ctx, channel: discord.TextChannel=None):
        """suggestions_chn (channel)"""
        await self.bot.pg_con.execute(
            """
            INSERT INTO settings (g_id, suggestion_chn_id)
                 VALUES ($1, $2)
            ON CONFLICT (g_id)
            DO
                UPDATE
                   SET suggestion_chn_id = EXCLUDED.suggestion_chn_id
            """, ctx.guild.id, channel.id if channel is not None else None
        )

        if channel is None:
            await ctx.send("There won't be a suggestions channel anymore")
        else:
            await ctx.send(f"The suggestions channel is {channel.mention}")

    @commands.command(name="rss_chn", brief="Set the rss channel feed. Don't mention a channel to disable rss")
    @commands.has_permissions(administrator=True)
    async def rss_channel(self, ctx, channel: discord.TextChannel = None):
        """rss_chn (channel)"""
        await self.bot.pg_con.execute(
            """
            INSERT INTO settings (g_id, rss_chn_id)
                 VALUES ($1, $2)
            ON CONFLICT (g_id)
            DO
                UPDATE
                   SET rss_chn_id = EXCLUDED.rss_chn_id
            """, ctx.guild.id, channel.id
        )

        if channel is None:
            await ctx.send("You have disabled your rss feed")
        else:
            await ctx.send(f"The rss feed will go in {channel.mention}")

    @commands.command(aliases=['pre'], brief="Change the prefix for the server (default is `!`)")
    @commands.check(lambda ctx: ctx.author.id == ctx.guild.owner.id)
    async def prefix(self, ctx, *, pre: str):
        '''prefix [prefix]'''
        await self.bot.pg_con.execute(
            """
            INSERT INTO settings (g_id, prefix)
                 VALUES ($1, $2)
            ON CONFLICT (g_id)
            DO
                UPDATE
                   SET prefix = EXCLUDED.prefix
            """, ctx.guild.id, pre
        )

        await ctx.send(f"New prefix: `{pre}`")

    @commands.command(hidden=True, brief="Insert all servers in db")
    @commands.check(is_bot_owner)
    async def find(self, ctx, this: bool = False):
        """find (this: bool)"""
        print(this)
        if this:
            await self.bot.pg_con.execute(
                """
                INSERT INTO settings (g_id)
                     VALUES ($1)
                """, ctx.guild.id
            )
        else:
            await self.bot.pg_con.executemany(
                """
                INSERT INTO settings (g_id)
                     VALUES ($1)
                """, [(guild.id,) for guild in self.bot.guilds]
            )

    @commands.command(brief='Set the currency name for the server. The `short` by default is same to the name')
    @commands.has_permissions(administrator=True)
    async def set_currency(self, ctx, name, short=None):
        """currency "[name]" "(short)\""""
        short = short or name

        await self.bot.pg_con.execute(
            """
            INSERT INTO currency (g_id, name, short)
                 VALUES ($1, $2, $3)
            ON CONFLICT (g_id)
            DO NOTHING
            """, ctx.guild.id, name, short
        )

    @commands.command(brief='Update the name and/or short of your currency')
    @commands.has_permissions(administrator=True)
    async def update_currency(self, ctx):
        """update_currency"""
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        name = None
        short = None

        await ctx.send("Do you want to update the name? [y/n]", delete_after=30)

        try:
            yes_no = (await self.bot.wait_for('message', timeout=30.0, check=check)).content.lower()
            if yes_no in ['yes', 'y']:
                await ctx.send("Type the new name", delete_after=300)
                name = (await self.bot.wait_for('message', timeout=30.0, check=check)).content.lower()

            await ctx.send("Do you want to update the short?", delete_after=30)
            yes_no = (await self.bot.wait_for('message', timeout=30.0, check=check)).content.lower()
            if yes_no in ["yes", "y"]:
                await ctx.send("Type the new short", delete_after=300)
                short = (await self.bot.wait_for('message', timeout=30.0, check=check)).content.lower()

        except asyncio.TimeoutError:
            await ctx.send("You didn't reply fast enough, sorry, you will have to do it again.")
            return


        if name is not None and short is not None:
            r = await self.bot.pg_con.execute(
                """
                UPDATE currency
                   SET name = $2,
                       short = $3
                 WHERE g_id = $1
                """, ctx.guild.id, name, short
            )
        elif name is not None:
            r = await self.bot.pg_con.execute(
                """
                UPDATE currency
                   SET name = $2,
                 WHERE g_id = $1
                """, ctx.guild.id, name
            )
        else:
            r = await self.bot.pg_con.execute(
                """
                UPDATE currency
                   SET short = $2,
                 WHERE g_id = $1
                """, ctx.guild.id, short
            )

        print(r)
        if r[-1] != '0':
            await ctx.send("Done")
        else:
            await ctx.send("You need to first set the currency")


def setup(bot):
    bot.add_cog(SetUp(bot))
