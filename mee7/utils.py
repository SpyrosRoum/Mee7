import time
import asyncio
import discord
from discord.ext import commands

def Nembed_warnings(ctx, page: int, pages: int, members, cur: int):
    embed = discord.Embed(
        color=ctx.author.color,
        timestamp=ctx.message.created_at
    )
    embed.set_author(name="Warnings", icon_url=ctx.bot.user.avatar_url)

    # If there somehow is no text, don't error
    text = ""
    for member_record in members[cur:cur+10]:
        member = ctx.guild.get_member(member_record['m_id'])
        if member is None:
            continue
        text += (f"Member: {member.mention}\n"
                f"Warnings: {member_record['warnings']}\n"
                f"----------\n")

    embed.description = text or "None"
    embed.set_footer(text=f"Page {page+1}/{pages}")

    return embed, cur


def Nembed_rss_feeds(ctx, page: int, pages: int, feeds, cur: int):
    embed = discord.Embed(
        color=ctx.author.color,
        timestamp=ctx.message.created_at
    )
    embed.set_author(name="Rss Feeds", icon_url=ctx.bot.user.avatar_url)

    text = ""
    for feed_record in feeds:
        text += (f"Title: {feed_record['name']}\n"
                 f"Url: {feed_record['link']}\n"
                 f"----------\n")

    embed.description = text or "None"
    embed.set_footer(text=f"Page {page+1}/{pages}")

    return embed, cur


def Nembed_triggers(ctx, page: int, pages: int, triggers, cur: int):
    embed = discord.Embed(
        color=ctx.author.color,
        timestamp=ctx.message.created_at
    )
    embed.set_author(name="Triggers", icon_url=ctx.bot.user.avatar_url)

    text = ""
    for trigger_record in triggers:
        text += (f"Trigger: {trigger_record['trigger']}\n"
                 f"Response: {trigger_record['response']}\n"
                 f"----------\n")

    embed.description = text or "None"
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
        return user != ctx.bot.user and r.message.id == msg.id

    t_end = time.time() + 120
    while time.time() < t_end:
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', check=check, timeout=60.0)
        except asyncio.TimeoutError:
            continue

        if str(reaction.emoji) == "➡":
            await msg.remove_reaction('➡', user)
            page += 1

            if page == pages:
                page -= 1
                continue


            new_embed, cur = func(ctx, page, pages, lst, cur + 10)
            await msg.edit(embed=new_embed)

        elif str(reaction.emoji) == "⬅":
            await msg.remove_reaction('⬅', user)
            page -= 1
            if page < 0:
                page = 0
                continue

            new_embed, cur = func(ctx, page, pages, lst, cur - 10)
            await msg.edit(embed=new_embed)

        elif str(reaction.emoji) == "❌":
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

async def get_short(bot: commands.Bot, g_id: int) -> str:
    """return the short for the currency in this server or \"\""""
    short = await bot.pg_con.fetchval(
        """
        SELECT short
          FROM currency
         WHERE g_id = $1
        """, g_id
    )

    return short or ""

async def get_name(bot: commands.Bot, g_id: int) -> str:
    """return the name for the currency in this server or \"\""""
    name = await bot.pg_con.fetchval(
        """
        SELECT name
          FROM currency
         WHERE g_id = $1
        """, g_id
    )

    return name or ""