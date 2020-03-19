import discord
from discord.ext import commands


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot=bot

    @commands.command(brief='Add an item to the store')
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, name, price: float, *, description=None):
        """add [name] [price] (description)"""
        r = await self.bot.pg_con.execute(
            """
            INSERT INTO store (g_id, item, price, description)
                 VALUES ($1, $2, $3, $4)
            ON CONFLICT (g_id, item)
            DO
                NOTHING
            """, ctx.guild.id, name.lower(), price, description
        )

        if r[-1] == '0':
            await ctx.send("That item already exists. Use `update` to update it")
        else:
            await ctx.send(f"Added {name}")

    @commands.command(brief='Update an item in the store if it exists')
    @commands.has_permissions(administrator=True)
    async def update(self, ctx, name, price: float, *, description=None):
        """update [name] [price] (description)"""
        r = await self.bot.pg_con.execute(
            """
            UPDATE store
               SET price = $3,
                   description = $4
             WHERE g_id = $1
               AND item = $2
            """, ctx.guild.id, name.lower(), price, description
        )

        if r[-1] == '0':
            await ctx.send("I didn't find the item")
        else:
            await ctx.send(f"Updated {name}")

    @commands.command(brief='Remove an item in the store if it exists')
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, name):
        """remove [name]"""
        r = await self.bot.pg_con.execute(
            """
            DELETE FROM store
                  WHERE g_id = $1
                    AND item = $2
            """, ctx.guild.id, name.lower()
        )

        if r[-1] == '0':
            await ctx.send("I didn't find the item")
        else:
            await ctx.send(f"Removed {name} from the store")


def setup(bot):
    bot.add_cog(Economy(bot))
