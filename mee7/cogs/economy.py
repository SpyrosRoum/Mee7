import discord
from discord.ext import commands

from utils import get_short


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Give any amount of money.")
    @commands.has_permissions(administrator=True)
    async def reward(self, ctx, member: discord.Member, amount: int):
        """reward [member] [amount]"""
        new_money = await self.bot.pg_con.fetchval(
            """
            INSERT INTO members (g_id, m_id, money)
                 VALUES ($1, $2)
            ON CONFLICT (g_id, m_id, (100 + $3))
            DO
                UPDATE
                   SET money = money + excluded.money
            RETURNING money
            """, ctx.guild.id, member.id, amount
        )
        short = await get_short(self.bot, ctx.guild.id)
        await ctx.send(f"{member} now has {new_money}{short}")


def setup(bot):
    bot.add_cog(Economy(bot))
