import discord
from discord.ext import commands

from utils import create_pages, Nembed_triggers

class Triggers(commands.Cog):
    def __init__(self, bot):
        self.bot=bot

    @commands.command(brief='Add a new trigger or update an old one')
    @commands.has_permissions(administrator=True)
    async def trigger_add(self, ctx, trigger, response):
        """trigger_add \"[trigger]\" \"[response]\""""
        if len(trigger) == 0:
            await ctx.send("Triggers can't be empty. Make sure to surround them in quotes (\"the trigger\")")
            return
        if len(response) == 0:
            await ctx.send("Responses can't be empty. Make sure to surround them in quotes (\"the response\")")
            return

        await self.bot.pg_con.execute(
            """
            INSERT INTO triggers (g_id, trigger_, response)
                 VALUES ($1, $2, $3)
            ON CONFLICT (g_id, trigger_)
            DO
                UPDATE
                   SET response = EXCLUDED.response
            """, ctx.guild.id, trigger.lower(), response
        )

        await ctx.send(f"New trigger `{trigger}` added")

    @commands.command(aliases=["trigger_rm", "trigger_rem"], brief='Remove a trigger')
    @commands.has_permissions(administrator=True)
    async def trigger_remove(self, ctx, *, trigger):
        """trigger_remove [trigger]"""
        response = await self.bot.pg_con.fetchval(
            """
            DELETE FROM triggers
                  WHERE g_id = $1
                    AND trigger_ = $2
            RETURNING response
            """, ctx.guild.id, trigger.lower()
        )

        if response is None:
            await ctx.send("I didn't find that trigger")
        else:
            await ctx.send(f"Trigger `{trigger}` with response `{response}` has been deleted")

    @commands.command(brief='Show a list of triggers')
    async def trigger_list(self, ctx):
        """trigger_list"""
        triggers = await self.bot.pg_con.fetch(
            """
            SELECT trigger_ AS trigger, response
              FROM triggers
             WHERE g_id = $1
            """, ctx.guild.id
        )

        if triggers == []:
            embed = discord.Embed(
                color=ctx.author.color,
                timestamp=ctx.message.created_at,
                description="You don't have any triggers"
            )
            await ctx.send(embed=embed)
        else:
            await create_pages(ctx, triggers, Nembed_triggers, "Triggers closed")

def setup(bot):
    bot.add_cog(Triggers(bot))
