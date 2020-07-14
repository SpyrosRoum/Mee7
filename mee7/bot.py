import os
from typing import Dict

import discord
from discord.ext import commands
import asyncpg


class Mee7(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pg_con: asyncpg.pool.Pool
        self.roles: Dict[int, int] = dict()

    async def create_pool(self, *, host, port, database, user, password):
        self.pg_con = await asyncpg.create_pool(host=host, port=port, database=database, user=user, password=password)
        await self.create_db()
        print("Connected to  the database.")

    async def create_db(self):
        with open("./DATA/schema.psql", 'r') as file:
            schema = file.read()
            await self.pg_con.execute(schema)

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print('------')

    @staticmethod
    async def get_custom_prefix(_bot, message: discord.Message):
        pre = await _bot.pg_con.fetchval(
            """
            SELECT prefix
              FROM settings
             WHERE g_id = $1
            """, message.guild.id
        )
        if pre is None:
            return '!'
        else:
            return commands.when_mentioned_or(pre)(_bot, message)


bot = Mee7(command_prefix=Mee7.get_custom_prefix)
# We remove the help command because we create a custom one in the help cog
bot.remove_command('help')

TOKEN = open('./DATA/TOKEN.txt', 'r').readline().strip()
DB_HOST = open('./DATA/DB_HOST.txt', 'r').readline().strip()
DB_PORT = open('./DATA/DB_PORT.txt', 'r').readline().strip()
DB_PASSWORD = open('./DATA/DB_PASS.txt', 'r').readline().strip()


async def get_auto_roles():
    roles = await bot.pg_con.fetch(
        """
        SELECT g_id, auto_role_id
          FROM settings
        """
    )

    for role in roles:
        bot.roles[role['g_id']] = role['auto_role_id']


for cog in os.listdir("./cogs"):
    if cog.endswith(".py") and not cog.startswith("_"):
        try:
            cog = f"cogs.{cog.replace('.py', '')}"
            bot.load_extension(cog)
        except Exception as err:
            print(f"{cog} can not be loaded:")
            raise err

bot.loop.run_until_complete(
    bot.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        database="mee7",
        user="postgres",
        password=DB_PASSWORD
    )
)
bot.loop.run_until_complete(get_auto_roles())
bot.run(TOKEN)
