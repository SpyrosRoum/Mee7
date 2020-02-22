import time
import asyncio
import discord

def Nembed_warnings(self, ctx, page: int, pages, members: list, cur: int):
    embed = discord.Embed(
        color=ctx.author.color,
        timestamp=ctx.message.created_at
    )
    embed.set_author(name="Warnings", icon_url=self.bot.user.avatar_url)

    text = ""
    for member in members[cur:cur+10]:
        try:
            member = ctx.guild.get_member(member[0])
            text += (f"Member: {member['m_id'].mention}\n"
                    f"Warnings: {member['warnings']}\n"
                    f"---------\n")
        except AttributeError:
            continue

    embed.description = text
    embed.set_footer(text=f"Page {page+1}/{pages}")

    return embed, cur

async def create_pages(self, ctx, lst, func, end_text):
    pages = 1 + (len(lst) // 10) if (len(lst) % 10) >= 1 else (len(lst) // 10)
    page = 0


    embed, cur = self.Nembed(ctx, page, pages, lst, 0)

    msg = await ctx.send(embed=embed)

    await msg.add_reaction('⬅')
    await msg.add_reaction('➡')
    await msg.add_reaction('❌')

    def check(r, user):
        return user.id != self.bot.user.id and ctx.guild.id == r.message.guild.id and r.message.id == msg.id

    t_end = time.time() + 120
    while time.time() < t_end:
        try:
            res, user = await self.bot.wait_for('reaction_add', check=check, timeout=60.0)
        except asyncio.TimeoutError:
            continue

        if str(res.emoji) == "➡":
            await msg.remove_reaction('➡', user)
            page += 1

            if page == pages:
                page -= 1
                continue


            new_embed, cur = self.Nembed_items(ctx, page, pages, lst, cur + 10)
            await msg.edit(embed=new_embed)

        elif str(res.emoji) == "⬅":
            await msg.remove_reaction('⬅', user)
            page -= 1
            if page < 0:
                page = 0
                continue

            new_embed, cur = self.Nembed_items(ctx, page, pages, lst, cur - 10)
            await msg.edit(embed=new_embed)

        elif str(res.emoji) == "❌":
            await msg.remove_reaction("❌", user)
            break

    await msg.remove_reaction('⬅', self.bot.user)
    await msg.remove_reaction('➡', self.bot.user)
    await msg.remove_reaction("❌", self.bot.user)

    embed = discord.Embed(
        color=ctx.author.color,
        description=f"`{ctx.prefix}{ctx.command}` to open again",
        timestamp=ctx.message.created_at
    )
    embed.set_author(name=end_text,
                        icon_url=self.bot.user.avatar_url)

    await msg.edit(embed=embed)
