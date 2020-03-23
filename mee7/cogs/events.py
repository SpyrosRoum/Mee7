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

        welcome = await self.bot.pg_con.fetchrow(
            """
            SELECT welcome_chn_id, welcome_msg
              FROM settings
             WHERE g_id = $1
            """, member.guild.id
        )

        welcome_chn_id = welcome['welcome_chn_id']
        welcome_msg = welcome['welcome_msg']

        if welcome_chn_id is None or welcome_msg is None:
            return

        welcome_chn = member.guild.get_channel(welcome_chn_id)
        if welcome_chn is None:
            return

        welcome_msg = welcome_msg.replace("{user}", member.mention)
        welcome_msg = welcome_msg.replace("{server}", member.guild)

        await welcome_chn.send(welcome_msg)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.pg_con.execute(
            """
            INSERT INTO settings (g_id)
                 VALUES ($1)
            """, guild.id
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        # Custom commands
        if message.author.bot:
            return

        prefix = await self.bot.get_prefix(message)
        if not message.content.startswith(tuple(prefix)):
            return

        ctx = await self.bot.get_context(message)
        if ctx.command is not None:
            return

        name = message.content.replace(ctx.prefix, '', 1).split()[0]
        cmd = await self.bot.pg_con.fetchrow(
            """
            SELECT *
              FROM commands
             WHERE g_id = $1
               AND cmd_name = $2
            """, message.guild.id, name
        )
        print("here")
        if cmd is None:
            return

        if cmd['cmd_type'] == 'text':
            await self.execute_text_type(message, cmd)

    async def execute_text_type(self, message, cmd):
        if cmd['cooldown'] is not None:
            # TODO Check cooldown
            pass

        if cmd['reply_in_dms']:
            await message.author.send(cmd['reply_with'])
        else:
            await message.channel.send(cmd['reply_with'])


def setup(bot):
    bot.add_cog(Events(bot))
