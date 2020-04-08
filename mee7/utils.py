import time
import asyncio
import discord

def Nembed_warnings(ctx, page: int, pages, members: list, cur: int):
    embed = discord.Embed(
        color=ctx.author.color,
        timestamp=ctx.message.created_at
    )
    embed.set_author(name="Warnings", icon_url=ctx.bot.user.avatar_url)

    text = ""
    for member_record in members[cur:cur+10]:
        try:
            member = ctx.guild.get_member(member_record['m_id'])
            text += (f"Member: {member.mention}\n"
                    f"Warnings: {member_record['warnings']}\n"
                    f"---------\n")
        except AttributeError:
            continue

    embed.description = text
    embed.set_footer(text=f"Page {page+1}/{pages}")
    return embed, cur

async def create_pages(ctx, lst, func, end_text):
    pages = 1 + (len(lst) // 10) if (len(lst) % 10) >= 1 else (len(lst) // 10)
    page = 0


    embed, cur = func(ctx, page, pages, lst, 0)

    msg = await ctx.send(embed=embed)

    await msg.add_reaction('⬅')
    await msg.add_reaction('➡')
    await msg.add_reaction('❌')

    def check(r, user):
        return user.id != ctx.bot.bot.user.id and ctx.guild.id == r.message.guild.id and r.message.id == msg.id

    t_end = time.time() + 120
    while time.time() < t_end:
        try:
            res, user = await ctx.bot.bot.wait_for('reaction_add', check=check, timeout=60.0)
        except asyncio.TimeoutError:
            continue

        if str(res.emoji) == "➡":
            await msg.remove_reaction('➡', user)
            page += 1

            if page == pages:
                page -= 1
                continue


            new_embed, cur = func(ctx, page, pages, lst, cur + 10)
            await msg.edit(embed=new_embed)

        elif str(res.emoji) == "⬅":
            await msg.remove_reaction('⬅', user)
            page -= 1
            if page < 0:
                page = 0
                continue

            new_embed, cur = func(ctx, page, pages, lst, cur - 10)
            await msg.edit(embed=new_embed)

        elif str(res.emoji) == "❌":
            await msg.remove_reaction("❌", user)
            break

    await msg.remove_reaction('⬅', ctx.bot.user)
    await msg.remove_reaction('➡', ctx.bot.user)
    await msg.remove_reaction("❌", ctx.bot.user)

    embed = discord.Embed(
        color=ctx.author.color,
        description=f"`{ctx.prefix}{ctx.command}` to open again",
        timestamp=ctx.message.created_at
    )
    embed.set_author(name=end_text,
                        icon_url=ctx.bot.user.avatar_url)

    await msg.edit(embed=embed)
