import discord
from discord.ext import commands


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot=bot

    @commands.command(brief="Make a suggestion for the server")
    async def suggest(self, ctx, *, suggestion):
        """suggest [suggestion]"""
        chn_id = await self.bot.pg_con.fetchval(
            """
            SELECT suggestion_chn_id
              FROM settings
             WHERE g_id = $1
            """, ctx.guild.id
        )

        if chn_id is None:
            await ctx.send("This server hasn't set up a channel for suggestions")
            return

        channel = ctx.guild.get_channel(chn_id)
        if channel is None:
            await ctx.send("It looks like the suggestions channel has been removed")
            return

        embed = discord.Embed(timestamp=ctx.message.created_at, description=f"{ctx.author} says:\n{suggestion}")
        msg = await channel.send(embed=embed)

        await msg.add_reaction('✅')
        await msg.add_reaction('❎')

        # TODO add the message to the db with the og author
        # check reacts, send dm to og author

def setup(bot):
    bot.add_cog(Misc(bot))
