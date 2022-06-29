import textwrap

import discord
from discord.ext import commands

from Utils.constants import images


class ShowLinksCog(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name='partners')
    async def show_partners(self, ctx: commands.Context):
        description = """\
        We are a Server that welcome and helps Newbies, Novice and Veterans
        Inspired by our companion Pelulu who always help us in our adventure. 
        ◦•●◉✿◦•●◉✿◦•●◉✿◦•●◉✿◦•●◉✿
        What our server provide
        『📖』Toram guides
        『🎁』 Giveaway
        『🎎』 Anime channels
        『🎉』 Exciting Events
        『📰』Toram News
        『👾』 Bot games
        『🎖️』Cool Roles
        『🤖』 Toram bot 
        『🏪』Market systems 
        『💎』Xtal loan
        『🗞️』Cy grimoire News
        ◦•●◉✿◦•●◉✿◦•●◉✿◦•●◉✿◦•●◉✿
        So what are you waiting for if you are a veteran player or newbie 
        Join us! and you will discover a new world beyond!
        [Invite Link](https://discord.gg/c4REk45zPw)
        """
        embed = discord.Embed(
            title="Toram's Pelulu",
            color=discord.Color.blurple(),
            description=textwrap.dedent(description)
        )
        embed.set_author(name='Partners', icon_url=images.SCROLL2)
        embed.set_thumbnail(url=images.PARTNER)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ShowLinksCog(bot))
