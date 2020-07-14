import asyncio

import discord
from discord.ext import commands

import feedparser
import aiohttp

from utils import create_pages, n_embed_rss_feeds


def format_html(text):
    text = text.replace("<p>", "    ")
    text = text.replace("<\\p>", "\n")
    text = text.replace("<\\br>", "\n")
    return text


async def send_entry(entry, chn: discord.TextChannel):
    embed = discord.Embed(
        title=entry['title'],
        description=format_html(entry['summary']),
        url=entry['link'],
    )

    if len(embed) > 1970:
        embed = discord.Embed(
            title=entry['title'],
            description=entry['summary'][:1900] + "...",
            url=entry['link'],
        )
    await chn.send(embed=embed)


async def get_feed(feed_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(feed_url) as resp:
            if resp.status != 200:
                return None

            data = await resp.read()
    return feedparser.parse(data)


class Rss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.loop.create_task(self.update_feeds())

    async def update_feed(self, feed_record=None, g_id=None, feed: feedparser.FeedParserDict = None, feed_id=None):
        if feed_record is not None:
            feed_id = feed_record['feed_id']
            feed = await get_feed(feed_record['feed_link'])
            if feed is None:
                return

            g_id = feed_record['g_id']

        chn_id = await self.bot.pg_con.fetchval(
            """
            SELECT rss_chn_id
                FROM settings
                WHERE g_id = $1
            """, g_id
        )
        if not chn_id:
            return

        chn = self.bot.get_channel(chn_id)
        if chn is None:
            return

        last_entries = await self.bot.pg_con.fetch(
            """
            SELECT feed_id, entry_id
              FROM rss_entries
             WHERE feed_id = $1
            """, feed_id
        )

        if not last_entries:
            for i, entry in enumerate(feed.entries):
                if i == 4:
                    break
                await send_entry(entry, chn)
                await asyncio.sleep(.25)

            e = feed.entries
            await self.bot.pg_con.executemany(
                """
                INSERT INTO rss_entries (feed_id, entry_id, title, summary, link, published)
                     VALUES ($1, $2, $3, $4, $5, $6)
                """,
                [(feed_id, e[i]['id'], e[i]['title'], e[i]['summary'], e[i]['link'], e[i]['published']) for i in
                 range(4)]
            )
        else:
            to_send = []
            for entry in feed.entries:
                ids = [past_entry['entry_id'] for past_entry in last_entries]
                if entry['id'] in ids:
                    break
                to_send.append(entry)

            if not to_send:
                return

            for entry in to_send:
                await send_entry(entry, chn)
                await asyncio.sleep(.25)

            if len(to_send) >= 4:
                await self.bot.pg_con.execute(
                    """
                    DELETE FROM rss_entries
                          WHERE feed_id = $1
                    """, feed_id
                )
            else:
                for i, past_entry in enumerate(last_entries[::-1]):
                    await self.bot.pg_con.execute(
                        """
                        DELETE FROM rss_entries
                              WHERE feed_id = $1
                                AND entry_id = $2
                        """, feed_id, past_entry['entry_id']
                    )
                    if i == len(to_send) - 1:
                        break
            await self.bot.pg_con.executemany(
                """
                INSERT INTO rss_entries (feed_id, entry_id, title, summary, link, published)
                     VALUES ($1, $2, $3, $4, $5, $6)
                """, [(feed_id, e['id'], e['title'], e['summary'], e['link'], e['published']) for e in to_send]
            )

    async def update_feeds(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            guilds_to_update = await self.bot.pg_con.fetch(
                """
                SELECT g_id, rss_chn_id
                  FROM settings
                 WHERE rss_chn_id IS NOT NULL
                """
            )
            if not guilds_to_update:
                await asyncio.sleep(3600)
                continue

            for guild_record in guilds_to_update:
                feed_records = await self.bot.pg_con.fetch(
                    """
                    SELECT *
                    FROM rss_feeds
                    WHERE g_id = $1
                    """, guild_record['g_id']
                )
                for feed_record in feed_records:
                    await self.update_feed(feed_record)
                    await asyncio.sleep(.5)

            await asyncio.sleep(3600)

    @commands.command(brief="Add an rss feed. If no name is given, the title from the feed will be used")
    @commands.has_permissions(administrator=True)
    async def rss_add(self, ctx, link, *, name=None):
        """rss_add [link] (name)"""
        for _ in range(2):
            feed = await get_feed(link)
            if feed is not None:
                break
        else:
            await ctx.send("The url didn't work out, make sure it's correct and/or try again later")
            return

        name = name or feed['feed']['title']
        feed_id = await self.bot.pg_con.fetchval(
            """
            INSERT INTO rss_feeds (g_id, feed_name, feed_link)
                 VALUES ($1, $2, $3)
            ON CONFLICT (g_id, feed_link)
            DO
                UPDATE
                   SET feed_name = EXCLUDED.feed_name
            RETURNING feed_id
            """, ctx.guild.id, name, link
        )
        txt = "If you have set an rss channel for your server, you will get updates for this feed starting.. now"
        await ctx.send(txt)
        await self.update_feed(g_id=ctx.guild.id, feed=feed, feed_id=feed_id)

    @commands.command(aliases=['rss_rem', 'rss_rm'], brief="Remove an rss feed based on link")
    @commands.has_permissions(administrator=True)
    async def rss_remove(self, ctx, link):
        """rss_remove [link]"""
        feed_id = await self.bot.pg_con.fetchval(
            """
            DELETE FROM rss_feeds
                  WHERE g_id = $1
                    AND feed_link = $2
              RETURNING feed_id
            """, ctx.guild.id, link
        )

        if feed_id is None:
            await ctx.send("I didn't find a feed with that url")
            return

        await self.bot.pg_con.execute(
            """
            DELETE FROM rss_entries
                    WHERE feed_id = $1
            """, feed_id
        )

        await ctx.send("You won't be getting updates for that feed anymore")

    @commands.command(aiases=["rss_feeds"], brief="A list of the rss feeds you have")
    async def rss_list(self, ctx):
        """rss_list"""
        feeds = await self.bot.pg_con.fetch(
            """
            SELECT feed_name AS name, feed_link AS link
              FROM rss_feeds
             WHERE g_id = $1
            """, ctx.guild.id
        )
        if not feeds:
            embed = discord.Embed(
                color=ctx.author.color,
                timestamp=ctx.message.created_at,
                description="You don't have any feeds"
            )
            await ctx.send(embed=embed)
            return

        await create_pages(ctx, feeds, n_embed_rss_feeds, "Feeds closed")


def setup(bot):
    bot.add_cog(Rss(bot))
