from discord.ext import commands
from discord.ext.commands import Context

from Utils.discord.error_handling.command_error import OnCommandError


class Error(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        await (await OnCommandError(self.bot, ctx.message, error).get_handler())


async def setup(bot):
    await bot.add_cog(Error(bot))
