import asyncio

from discord.ext import commands


class ReactionRoles(commands.Cog, name="Reaction roles"):
    def __init__(self, bot):
        self.bot = bot

    async def get_role_guild(self, payload):
        role_id = await self.bot.pg_con.fetchval(
            """
            SELECT role_id
              FROM react_role
             WHERE g_id = $1
               AND msg_id = $2
               AND emoji = $3
            """, payload.guild_id, payload.message_id, str(payload.emoji)
        )

        if role_id is None:
            return None, None

        guild = self.bot.get_guild(payload.guild_id)
        return guild.get_role(role_id), guild

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # TODO test
        role, guild = await self.get_role_guild(payload)

        if role is None:
            return

        member = guild.get_member(payload.user_id)
        try:
            await member.add_roles(role)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # TODO test
        role, guild = await self.get_role_guild(payload)

        if role is None:
            return

        member = guild.get_member(payload.user_id)
        try:
            await member.remove_roles(role)
        except Exception:
            pass

    @commands.command(brief="Set up a message for adding roles when reacting")
    async def add_message(self, ctx, *, text: commands.clean_content):
        """add_message [the message]"""
        await ctx.message.delete()

        txt = ("Send me an emoji that will be used for a role and the role that it will add. [👦 some_role] "
               "where `some_role` is a mention, id or name of a role\n"
               "Note that if you say a second time the same emoji, it will over-write the previous one\n"
               "Send `stop` if you don't want to add any other emojis")
        instr = await ctx.send(txt)

        emoji_role = dict()
        messages_to_delete = []
        while True:
            try:
                def check(_msg):
                    return _msg.author == ctx.author and _msg.channel == ctx.message.channel

                msg = await self.bot.wait_for("message", check=check, timeout=120)
            except asyncio.TimeoutError:
                await ctx.send("You took too long to reply, sorry :/")
                return

            if msg.content.lower() == "stop":
                await msg.delete()
                break

            if len(content_lst := msg.content.split()) != 2:
                await ctx.send("Please send something to the format of:\nemoji role", delete_after=120)
                await msg.delete()
                continue

            messages_to_delete.append(msg)
            emoji = content_lst[0]
            if emoji in emoji_role:
                tmp = await ctx.send("You can't have the same emoji more than once in the same message")
                messages_to_delete.append(tmp)
                continue

            await msg.add_reaction('👍')

            role = await commands.RoleConverter().convert(ctx, content_lst[1])
            if role is None:
                tmp = await ctx.send("Please send messages to the format of\n`emoji role`")
                messages_to_delete.append(tmp)
                continue

            emoji_role[emoji] = role.id

        async with msg.channel.typing():
            for message in messages_to_delete:
                await message.delete()
                await asyncio.sleep(.25)

            msg = await ctx.send(text)

            await self.bot.pg_con.executemany(
                """
                INSERT INTO react_role (g_id, msg_id, emoji, role_id)
                     VALUES ($1, $2, $3, $4)
                """, [(ctx.guild.id, msg.id, emoji, role_id) for emoji, role_id in emoji_role.items()]
            )

            for emoji in emoji_role:
                await msg.add_reaction(emoji)

        await instr.delete()


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
