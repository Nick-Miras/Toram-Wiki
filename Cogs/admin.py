from Utils import PaginationItem, PaginatorView, PageSource, Paginator
from discord.ext import commands
import discord


class Source(PageSource):
    async def format_page(self, data: list[PaginationItem]):
        embed = discord.Embed()
        for item in data:
            embed.add_field(name=item.name, value='\u200b', inline=False)
        return embed


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name='test')
    async def raw_test(self, ctx: commands.Context):
        text = [i for i in range(10)]
        data = [PaginationItem(name=item) for item in text]
        paginator = Paginator(source=Source(data, per_page=3))
        await ctx.send('Test', view=PaginatorView(ctx, paginator=paginator))


def setup(bot):
    bot.add_cog(Test(bot))
