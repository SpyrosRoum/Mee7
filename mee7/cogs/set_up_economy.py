import asyncio

import discord
from discord.ext import commands


class SetUpEco(commands.Cog, name="Set up Economy"):
    def __init__(self, bot):
        self.bot=bot


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
                   SET name = $2
                 WHERE g_id = $1
                """, ctx.guild.id, name
            )
        else:
            r = await self.bot.pg_con.execute(
                """
                UPDATE currency
                   SET short = $2
                 WHERE g_id = $1
                """, ctx.guild.id, short
            )

        if r[-1] != '0':
            await ctx.send("Done")
        else:
            await ctx.send("You need to first set the currency")


def setup(bot):
    bot.add_cog(SetUpEco(bot))
