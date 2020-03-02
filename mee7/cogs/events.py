import discord
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if (role_id := self.bot.roles[member.guild.id]) is None:
            return

        role = member.guild.get_role(role_id)
        if role is not None:
            await member.add_roles(role, reason="Auto role, given upon entry")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.pg_con.execute(
            """
            INSERT INTO settings (g_id)
                 VALUES ($1)
            """, guild.id
        )

    # TODO on guild_remove event?


def setup(bot):
    bot.add_cog(Events(bot))
