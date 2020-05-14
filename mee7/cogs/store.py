import discord
from discord.ext import commands


class Store(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            await ctx.send(f"That item already exists. Use `{ctx.prefix}update` to update it")
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

    @commands.command(brief='Remove an item from the store if it exists')
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

    @commands.command(brief='Buy an item')
    async def buy(self, ctx, name, amount: int = 1):
        """buy [name] (amount=1)"""
        # TODO try to do this more efficient for the db
        item = await self.bot.pg_con.fetchrow(
            """
            SELECT item_id, item, price, description 
              FROM store
             WHERE g_id = $1
               AND item = $2 
            """, ctx.guild.id, name.lower()
        )

        if item is None:
            await ctx.send("I didn't find this item.")

        member_r = await self.bot.pg_con.fetchrow(
            """
            INSERT INTO members (g_id, m_id) 
            VALUES ($1, $2)
            ON CONFLICT (g_id, m_id)
            DO NOTHING 
            RETURNING id, money
            """, ctx.guild.id, ctx.author.id
        )

        cur = await self.bot.pg_con.fetchval(
            """
            SELECT short
              FROM currency
             WHERE g_id = $1
            """, ctx.guild.id
        )
        cur = cur or ""

        if (price := item['price'] * amount) > member_r['money']:
            await ctx.send(f"You don't have enough money to buy {amount} {name}. "
                           f"You need another {price - member_r['money']} {cur}")
        else:
            new_amount = await self.bot.pg_con.fetchval(
                """
                INSERT INTO inventories (id, item_id, amount)
                VALUES ($1, $2, $3)
                ON CONFLICT (id, item_id)
                DO UPDATE 
                SET amount = amount + excluded.amount               
                RETURNING amount
                """, member_r['id'], item['item_id'], amount
            )
            await self.bot.pg_con.execute(
                """
                UPDATE members
                SET money = $2
                WHERE id = $1
                """, member_r['id'], member_r['money'] - price
            )
            await ctx.send(f"You now have {new_amount} {name}")


def setup(bot):
    bot.add_cog(Store(bot))
