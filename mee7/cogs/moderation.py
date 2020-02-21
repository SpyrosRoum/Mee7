import discord
from discord.ext import commands


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
        await ctx.send(f"{member.mention} banned by {ctx.author}. [{reason}]")

    @commands.command(aliases=['clear'], brief="Purge a channel")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """purge [amount]"""
        channel = ctx.channel
        await channel.purge(limit=amount+1)
        await ctx.send(f"{amount} messages deleted")

    @commands.command(brief="Mute a member")
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member):
        """mute [member]"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role is None:
            # TODO: test this is a correct role
            muted_role = await ctx.guild.create_role(permissions=discord.Permissions(send_messages=False), name="Muted")

        await ctx.send(f"{member.mention} has been muted")

    @commands.command(brief="Unmute a member")
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member):
        """unmute [member]"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role is None:
            await ctx.send("This person is not muted")

        await member.remove_roles(muted_role)
        await ctx.send(f"{member.mention} has been unmuted")


    # TODO warn, unwarn, warnings (list), lock, unlock (channels)

def setup(bot):
    bot.add_cog(Moderation(bot))
