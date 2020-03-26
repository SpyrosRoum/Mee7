import asyncio

import discord
from discord.ext import commands


class ReactionRoles(commands.Cog, name="Reaction roles"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Set up a message for adding roles when reacting")
    async def add_message(self, ctx, *, text: commands.clean_content):
        """add_message [the message]"""
        await ctx.message.delete()

        instr = await ctx.send("Send me an emoji that will be used for a role and the role that it will add. [👦 @some_role]\n"
                               "Note that if you say a second time the same emoji, it will over-write the previous one\n"
                               "Send `stop` if you don't want to add any other emojis")

        emoji_role = dict()
        messages = []
        while True:
            try:
                msg = await self.bot.wait_for("message", check=lambda msg: msg.author==ctx.author and msg.channel==ctx.message.channel, timeout=120)
            except asyncio.TimeoutError:
                await ctx.send("You took too long to reply, sorry :/")
                return

            if msg.content.lower() == "stop":
                await msg.delete()
                break

            if len(content_lst := msg.content.split()) > 2:
                await ctx.send("Please send something to the format of:\nemoji @role", delete_after=120)
                await msg.delete()
                continue

            messages.append(msg)
            emoji = content_lst[0]
            if emoji in emoji_role:
                msg = await ctx.send("You can't have the same emoji more than once in the same message")
                messages.append(msg)
                continue

            await msg.add_reaction('👍')

            try:
                role_id = msg.raw_role_mentions[0]
            except IndexError:
                await ctx.send("Please send messages in the format of `emoji @role`", delete_after=120)
                continue

            emoji_role[emoji] = role_id

        async with msg.channel.typing():
            for message in messages:
                await message.delete()
                await asyncio.sleep(.25)

            msg = await ctx.send(text)

            await self.bot.pg_con.executemany(
                """
                INSERT INTO react_role (g_id, msg_id, emoji, role_id)
                     VALUES ($1, $2, $3, $4)
                """, [(ctx.guild.id, msg.id, emoji, role_id) for emoji, role_id in emoji_role.items()]
            )

            for emoji in emoji_role.keys():
                await msg.add_reaction(emoji)

        await instr.delete()



def setup(bot):
    bot.add_cog(ReactionRoles(bot))
