import discord
from discord.ext import commands

import asyncio

from utils import create_pages, Nembed_warnings

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Kick a member")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason"):
        """kick [member]"""
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} kicked by {ctx.author}. [{reason}]")

    @commands.command(brief="Ban a member")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason"):
        """ban [member]"""
        await member.ban(reason=reason)
        await ctx.send(f"{member} banned by {ctx.author}. [{reason}]")

    @commands.command(brief='Unban a member')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User):
        """unban [user]"""
        try:
            await ctx.guild.unban(user)
            await ctx.send(f"Unbaned {user}")
        except Exception:
            await ctx.send("I wasn't able to do that :/")


    @commands.command(brief='Temporarily bans a user from the server')
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, member: discord.User, duration, *, reason=None):
        """tempban [member] [duration in hour(s)] (reason)"""
        await ctx.guild.ban(user=member, reason=reason)
        await ctx.send(f"Banned {member} for {duration} hours")

        #* Should I do somehting other than sleep?
        await asyncio.sleep(duration*3600)

        await ctx.guild.unban(member, reason="End of tempban")

    @commands.command(aliases=['clear'], brief="Purge a channel")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int, member: discord.Member=None):
        """purge [amount] (member)"""
        if member is not None:
            await ctx.channel.purge(limit=amount, check=lambda msg: msg.author == member)
        else:
            await ctx.channel.purge(limit=amount+1)

        await ctx.send(f"{amount} messages deleted", delete_after=10)

    @commands.command(brief="Mute a member")
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member):
        """mute [member]"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role is None:
            # TODO test this is a correct role
            muted_role = await ctx.guild.create_role(permissions=discord.Permissions(send_messages=False), name="Muted")

        await ctx.send(f"{member.mention} has been muted")

    @commands.command(brief="Unmute a member")
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member):
        """unmute [member]"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role is None:
            await ctx.send("This person is not muted. \nIf he is, try mutting them again")

        await member.remove_roles(muted_role)
        await ctx.send(f"{member.mention} has been unmuted")

    @commands.command(brief='Temporarily mute a member')
    @commands.has_permissions(manage_messages=True)
    async def tempmute(self, ctx, member: discord.Member, duration: float):
        """tempmute [member] [duation in hours]"""
        await ctx.invoke(self.mute, member)
        #* Should I do somehting other than sleep?
        await asyncio.sleep(duration*3600)
        await ctx.invoke(self.unmute, member)

    @commands.command(brief='Give a warning to someone')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, reason=None):
        """warn [member] (reason)"""
        warnings = await self.bot.pg_con.fetchval(
            """
            INSERT INTO members (g_id, m_id, warnings)
                 VALUES ($1, $2, $3)
            ON CONFLICT (g_id, m_id)
            DO
                UPDATE
                   SET warnings = members.warnings + 1
            RETURNING warnings
            """, ctx.guild.id, member.id, 1
        )

        await ctx.send(f"{member.mention} you have been warned {f'[{reason}] ' if reason else ''}and have {warnings} warnings")

    @commands.command(brief='Remove a warning from someone')
    @commands.has_permissions(manage_messages=True)
    async def unwarn(self, ctx, member: discord.Member):
        """unwarn [member]"""
        warnings = await self.bot.pg_con.fetchval(
            """
            UPDATE members
               SET warnings = warnings - 1
             WHERE g_id = $1
               AND m_id = $2
               AND warnings > 0
            RETURNING warnings
            """, ctx.guild.id, member.id
        )

        await ctx.send(f"{member.mention} you now have {warnings} warnings")

    @commands.command(brief='Show the warnings of a member or everyone')
    async def warnings(self, ctx, member: discord.Member=None):
        """warnings (member)"""
        if member is not None:
            warnings = await self.bot.pg_con.fetchval(
                """
                SELECT warnings
                  FROM members
                 WHERE g_id = $1
                   AND m_id = $2
                """, ctx.guild.id, member.id
            )
            warnings = warnings or 0
            embed = discord.Embed(
                color=ctx.author.color,
                timestamp=ctx.message.created_at
            )
            embed.set_author(name="Warnings", icon_url=member.avatar_url)

            text = (f"Member: {member.mention}\n"
                    f"Warnings: {warnings}\n")
            embed.description = text

            await ctx.send(embed=embed)
        else:
            warnings = await self.bot.pg_con.fetch(
                """
                SELECT warnings
                  FROM members
                 WHERE g_id = $1
                """
            )
            await create_pages(ctx, warnings, Nembed_warnings, "Warnings closed")

    @commands.command(brief='Make an announcements')
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, text):
        """announce [channel] [announcement]"""
        embed = discord.Embed(title="Announcement", description=text, color=ctx.author.color, timestamp=ctx.message.created_at)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await channel.send(embed=embed)

    # TODO lock, unlock (channels)

def setup(bot):
    bot.add_cog(Moderation(bot))
