import asyncio

import discord
from discord.ext import commands

import feedparser
import aiohttp


class Rss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.loop.create_task(self.update_feeds())

    async def send_entry(self, entry, chn):
        embed = discord.Embed(
            title=entry['title'],
            description=entry['summary'],
            url=entry['link'],
        )
        await chn.send(embed=embed)

    async def update_feed(self, feed_record = None, feed: feedparser.FeedParserDict = None, feed_id = None):
        if feed_record is not None:
            feed_id = feed_record['feed_id']
            feed = await self.get_feed(feed_record['feed_url'])
            if feed is None:
                return

        chn_id = await self.bot.pg_con.fetchval(
            """
            SELECT rss_chn_id
                FROM settings
                WHERE g_id = $1
            """, feed_record['g_id']
        )
        if chn_id is None:
            return
        chn = self.bot.get_channel(chn_id)
        if chn is None:
            return

        last_entries = await self.bot.pg_con.fetch(
            """
            SELECT *
                FROM rss_entries
                WHERE feed_id = $1
            """, feed_id
        )

        if last_entries == []:
            for i, entry in enumerate(feed.entries):
                if i == 4:
                    break
                await self.send_entry(entry, chn)
                await asyncio.sleep(.25)

            e = feed.entries
            await self.bot.pg_con.executemany(
                """
                INSERT INTO rss_entries (feed_id, entry_id, title, summary, link, published)
                     VALUES ($1, $2, $3, $4, $5, $6)
                """, [(feed_id, e[i]['id'], e[i]['title'], e[i]['summary'], e[i]['link'], e[i]['published']) for i in range(4)]
            )
        else:
            to_send = []
            while True:
                for entry in feed.entries:
                    if entry['id'] in last_entries:
                        break
                    else:
                        to_send.append(entry)
            for entry in to_send:
                await self.send_entry(entry, chn)
                await asyncio.sleep(.25)

            if len(to_send) >= 4:
                await self.bot.pg_con.execute(
                    """
                    DELETE FROM rss_entries
                          WHERE feed_id = $1
                    """, feed_id
                )
            else:
                for past_entry in last_entries[::-1]:
                    await self.bot.pg_con.execute(
                        """
                        DELETE FROM rss_entries
                              WHERE feed_id = $1
                                AND entry_id = $2
                        """, feed_id, past_entry['entry_id']
                    )
            await self.bot.pg_con.executemany(
                """
                INSERT INTO rss_entries (feed_id, entry_id, title, summary, link, published)
                     VALUES ($1, $2, $3, $4, $5, $6)
                """, [(feed_id, e['id'], e['title'], e['summary'], e['link'], e['published']) for e in to_send]
            )



    async def update_feeds(self):
        await self.bot.wait_until_ready()

        while self.bot.is_closed():
            guilds_to_update = await self.bot.pg_con.fetch(
                """
                SELECT g_id, rss_chn_id
                  FROM settings
                 WHERE rss_chn_id IS NOT NULL
                """
            )
            if guilds_to_update == []:
                await asyncio.sleep(3600)
                continue

            for guild_record in guilds_to_update:
                feed_records = await self.bot.pg_con.fetch(
                    """
                    SELECT *
                    FROM rss_feeds
                    WHERE g_id = $1
                    """, guild_record['rss_chn_id']
                )
                for feed_record in feed_records:
                    await self.update_feed(feed_record)
                    await asyncio.sleep(.5)

            await asyncio.sleep(3600)

    async def get_feed(self, feed_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(feed_url) as resp:
                if resp.status != 200:
                    return None

                data = await resp.read()

        return feedparser.parse(data)

    @commands.command(brief="Add an rss feed. If no name is given, the title from the feed will be used")
    async def add_rss(self, ctx, link, *, name=None):
        """add_rss [link] (name)"""
        for _ in range(2):
            feed = await self.get_feed(link)

            if feed is not None:
                break
        else:
            await ctx.send("The url didn't work out, make sure it's correct and/or try again later")
            return

        name = name or feed['title']

        feed_id = await self.bot.pg_con.fetchval(
            """
            INSERT INTO rss_feeds (g_id, feed_name, feed_link)
                 VALUES ($1, $2, $3)
            ON CONFLICT (g_id, feed_name)
            DO
                UPDATE
                   SET feed_link = EXCLUDED.feed_link
            RETURNING feed_id
            """, ctx.guild.id, name, link
        )

        await ctx.send("If you have set an rss channel for your server, you will get updates for this feed starting.. now")
        await self.update_feed(feed=feed, feed_id=feed_id)





def setup(bot):
    bot.add_cog(Rss(bot))
