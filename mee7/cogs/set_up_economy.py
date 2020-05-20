import asyncio

from utils import get_name

from discord.ext import commands


class SetUpEco(commands.Cog, name="Set up Economy"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, brief="Configure economy related commands", name="set")
    async def set_(self, ctx):
        """set [command]"""
        pass

    @set_.command(brief='Set the currency name for the server. The `short` by default is same to the name')
    @commands.has_permissions(administrator=True)
    async def currency(self, ctx, name, short=None):
        """set currency "[name]" "(short)\""""
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

    async def set_min_max(self, g_id, cmd_name, min_, max_):
        await self.bot.pg_con.execute(
            """
            INSERT INTO eco_settings (g_id, cmd_name, min, max) 
                 VALUES ($1, $2, $3, $4)
            ON CONFLICT (g_id, cmd_name)
            DO 
                UPDATE 
                   SET (min, max) = (excluded.min, excluded.max)
            """, g_id, cmd_name, min_, max_
        )

    @set_.command(brief=("Set the min and max money someone can get from the command `slut`. "
                         "Min and max can be the same"))
    async def slut(self, ctx, min_: float, max_: float):
        """set slut [min] [max]"""
        if min_ > max_:
            await ctx.send("The minimum money can't be more than the maximum")
            return

        await self.set_min_max(ctx.guild.id, "slut", min_, max_)

        cur_name = await get_name(self.bot, ctx.guild.id)
        await ctx.send(f"`slut` will now reward between {min_} and {max_} {cur_name}")

    @set_.command(brief=("Set the min and max money someone can get from the command `work`. "
                         "Min and max can be the same"))
    async def work(self, ctx, min_: float, max_: float):
        """set work [min] [max]"""
        if min_ > max_:
            await ctx.send("The minimum money can't be more than the maximum")
            return

        await self.set_min_max(ctx.guild.id, "work", min_, max_)

        cur_name = await get_name(self.bot, ctx.guild.id)
        await ctx.send(f"`work` will now reward between {min_} and {max_} {cur_name}")

    @set_.command(brief=("Set the min and max money someone can get from the command `gamble`. "
                         "Min and max can be the same"))
    async def gamble(self, ctx, min_: float, max_: float):
        """set gamble [min] [max]"""
        if min_ > max_:
            await ctx.send("The minimum money can't be more than the maximum")
            return

        await self.set_min_max(ctx.guild.id, "gamble", min_, max_)

        cur_name = await get_name(self.bot, ctx.guild.id)
        await ctx.send(f"`gamble` will now reward between {min_} and {max_} {cur_name}")

    @set_.command(brief=("Set the min and max money someone can get from the command `crime`. "
                         "Min and max can be the same"))
    async def crime(self, ctx, min_: float, max_: float):
        """set crime [min] [max]"""
        if min_ > max_:
            await ctx.send("The minimum money can't be more than the maximum")
            return

        await self.set_min_max(ctx.guild.id, "crime", min_, max_)

        cur_name = await get_name(self.bot, ctx.guild.id)
        await ctx.send(f"`crime` will now reward between {min_} and {max_} {cur_name}")




def setup(bot):
    bot.add_cog(SetUpEco(bot))
