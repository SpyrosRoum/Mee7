import discord
from discord.ext import commands


class SetUp(commands.Cog, name="Set up"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx):
        # TODO test
        pass

    @welcome.command(aliases=['chn'], brief='Set the channel for the welcome message')
    @commands.has_permissions(administrator=True)
    async def channel(self, ctx, channel: discord.TextChannel=None):
        """channel (channel)"""
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
        """message [message]"""
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
        """role (role)"""
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
            await ctx.send(f"{role.name} will be given when someone joins.")

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
            await ctx.send(f"The suggestions channel is {channel}")

def setup(bot):
    bot.add_cog(SetUp(bot))
