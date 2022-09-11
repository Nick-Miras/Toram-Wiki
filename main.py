import os
import re
from typing import Iterable

import discord
from discord import Interaction
from discord.app_commands import CommandTree, AppCommandError
from discord.ext import commands

from Utils.discord.error_handling.interaction_error import OnInteractionError
from database import get_mongodb_client
from database.models import WhiskeyDatabase


async def load_cogs(bot: commands.Bot):  # Loads all the Cogs
    skip_files = ('exceptions', 'system')  # DO NOT LOAD THESE FILES
    file_paths = [r for r, _, _ in os.walk('./Cogs') if 'cache' not in r]

    for path in file_paths:
        path_name = re.sub(r'[\\/]', '.', path[2:])
        for filename in os.listdir(path):
            if filename.endswith('.py'):
                if filename.startswith(skip_files):
                    print(f'Skipping {filename}')
                    continue

                extension = f'{path_name}.{filename[:-3]}'
                try:
                    await bot.load_extension(extension)
                except commands.NoEntryPointError:
                    print(f'NoEntryPoint: {extension}')


class MyTree(CommandTree):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super(MyTree, self).__init__(client=bot)

    async def on_error(self, interaction: Interaction, error: AppCommandError) -> None:
        await (await OnInteractionError(self.bot, interaction, error).get_handler())


class MyBot(commands.Bot):
    def __init__(self, application_id: int = None):
        mentionable = discord.AllowedMentions(
            replied_user=False
        )
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=self.fetch_prefix,
            allowed_mentions=mentionable,
            intents=intents,
            help_command=None,
            tree_cls=MyTree,
            application_id=application_id
        )
        if not hasattr(self, 'uptime'):
            self.uptime = discord.utils.utcnow()

    @staticmethod
    def fetch_prefix(bot: commands.Bot, message: discord.Message):
        def inner() -> str:
            if message.guild is None:
                return '$'  # default prefix
            return str(
                WhiskeyDatabase(get_mongodb_client()).discord_guilds.find_one({'_id': message.guild.id})['prefix']
            )
        return commands.when_mentioned_or(inner())(bot, message)

    async def copy_global_to(self, guilds: Iterable[int]):
        for guild in guilds:
            self.tree.copy_global_to(guild=discord.Object(guild))

    async def setup_hook(self) -> None:
        await load_cogs(self)

    async def on_ready(self):
        await self.copy_global_to(guild.id for guild in self.guilds)
        await self.tree.sync()
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


bot = MyBot(application_id=int(os.environ['APPLICATION_ID']))


@bot.event
async def on_message(message: discord.Message):
    """If the bot gets mentioned
    """
    if message.guild:
        cnt = message.content.split()  # the split message into list
        if (cnt and message.author.bot is False and len(cnt) == 1) and (re.match(f'<@!?{bot.user.id}>', cnt[0])):
            prefix = await bot.get_prefix(message)
            embed = discord.Embed(
                description=f"Hello {message.author.mention}!\n`{prefix[2]}help` for more information")
            await message.channel.send(embed=embed)
    await bot.process_commands(message)


bot.run(os.environ['TOKEN'])
