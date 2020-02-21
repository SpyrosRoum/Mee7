import discord
from discord.ext import commands
import asyncpg

import os

async def get_prefix(bot, message):
    pre = await bot.pg_con.fetchval(
        """
        SELECT prefix
          FROM settings
         WHERE g_id = $1
        """, message.guild.id
    )
    if pre is None:
        return '!'
    else:
        return commands.when_mentioned_or(pre)(bot, message)


bot = commands.Bot(command_prefix=get_prefix)
bot.remove_command('help')

TOKEN = open('mee7/DATA/TOKEN.txt', 'r').readline().strip()
DB_HOST = open('mee7/DATA/DB_HOST.txt', 'r').readline().strip()
DB_PORT = open('mee7/DATA/DB_PORT.txt', 'r').readline().strip()
DB_PASSWORD = open('mee7/DATA/DB_PASS.txt', 'r').readline().strip()


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print('------')


async def create_db_pool():
    # TODO change host and password before delivering
    bot.pg_con = await asyncpg.create_pool(host=DB_HOST, port=DB_PORT, database="mee7", user="postgres", password=DB_PASSWORD)
    print("Connected to database")

async def get_auto_roles():
    roles = bot.pg_con.fetch(
        """
        SELECT g_id, auto_role_id
          FROM settings
        """
    )

    bot.roles = dict()
    for role in roles:
        bot.roles[role['g_id']] = role['auto_role_id']


for cog in os.listdir("./mee7/cogs"):
    if cog.endswith(".py") and not cog.startswith("_"):
        try:
            cog = f"cogs.{cog.replace('.py', '')}"
            bot.load_extension(cog)
        except Exception as e:
            print(f"{cog} can not be loaded:")
            raise e


bot.loop.run_until_complete(create_db_pool())
bot.loop.run_until_complete(get_auto_roles())
bot.run(TOKEN)
