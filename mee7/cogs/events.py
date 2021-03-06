import time

import discord
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_trigger(self, message):
        triggers = await self.bot.pg_con.fetch(
            """
            SELECT trigger_ as trigger, response
              FROM triggers
             WHERE g_id = $1
            """, message.guild.id
        )

        if triggers == []:
            return

        for trigger_record in triggers:
            if trigger_record['trigger'] in message.content.lower():
                await message.channel.send(f"{message.author.mention} {trigger_record['response']}")
                return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if (role_id := self.bot.roles.get(member.guild.id)) is None:
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
        welcome_msg = welcome_msg.replace("{server}", member.guild.name)

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
            await self.check_trigger(message)
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

    async def check_cooldown(self, message: discord.Message, cmd):
        last_did = await self.bot.pg_con.fetchval(
            """
            SELECT did_at
                FROM cooldown
                WHERE g_id = $1
                AND m_id = $2
                AND cmd_name = $3
            """, message.guild.id, message.author.id, cmd['cmd_name']
        )
        if last_did is None or last_did + cmd['cooldown'] < time.time():
            return (True, 0) # Meaning the can do it

        else:
            return (False, (last_did + cmd['cooldown']) - int(time.time()))

    async def update_cooldown(self, message, cmd):
        await self.bot.pg_con.execute(
            """
            INSERT INTO cooldown (g_id, m_id, cmd_name, did_at)
                    VALUES ($1, $2, $3, $4)
            ON CONFLICT (g_id, m_id, cmd_name)
            DO
                UPDATE
                    SET did_at = EXCLUDED.did_at
            """, message.guild.id, message.author.id, cmd['cmd_name'], int(time.time())
        )

    async def execute_text_type(self, message, cmd):
        if cmd['cooldown'] is not None:
            if has_cooldown := (await self.check_cooldown(message, cmd)):
                await self.update_cooldown(message, cmd)
            else:
                seconds_left = has_cooldown[1]
                await message.channel.send(f"You are in cooldown. try again in {seconds_left} seconds")

        if cmd['reply_in_dms']:
            await message.author.send(cmd['reply_with'])
        else:
            await message.channel.send(cmd['reply_with'])

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # For suggestions
        guild_id = payload.guild_id
        msg_id = payload.message_id
        user_id = payload.user_id

        suggestion = await self.bot.pg_con.fetchrow(
            """
            SELECT m_id, summary
              FROM suggestions
             WHERE g_id = $1
               AND msg_id = $2
               AND approved IS NULL
            """, guild_id, msg_id
        )

        if suggestion is None:
            return

        if str(payload.emoji) not in ['✅', '❎']:
            return

        guild = self.bot.get_guild(guild_id)
        member = guild.get_member(user_id)

        if not member.guild_permissions.administrator:
            return

        approved = str(payload.emoji) == '✅'

        await self.bot.pg_con.execute(
            """
            UPDATE suggestions
               SET approved = $2
             WHERE msg_id = $1
            """, msg_id, approved
        )

        author = guild.get_member(suggestion['m_id'])
        if author is None:
            return

        try:
            if approved:
                txt = f"Yay, your suggestion in {guild.name} to `{suggestion['summory']}` **got approved**"
                await author.send(txt)
            else:
                txt = f"I'm sorry, your suggestion in {guild.name} to `{suggestion['summary']}` **got declined**"
                await author.send(txt)
        except discord.Forbidden:
            pass


def setup(bot):
    bot.add_cog(Events(bot))
