import os
import re

import discord
from discord.ext import commands

from Utils.database import Database


def cog_loader(bot):  # Loads all the Cogs
    skip_files = ()  # DO NOT LOAD THIS FILES
    file_paths = [r for r, _, _ in os.walk('./Cogs') if 'pycache' not in r]

    for path in file_paths:
        path_name = re.sub(r'[\\/]', '.', path[2:])
        for filename in os.listdir(path):
            if filename.endswith('.py') and not filename.startswith(skip_files):
                extension = f'{path_name}.{filename[:-3]}'
                try:
                    bot.load_extension(extension)
                except commands.NoEntryPointError:
                    print(f'NoEntryPoint: {extension}')


def fetch_prefix(bot: commands.Bot, message: discord.Message) -> str:
    default_prefix = '$'
    if message.guild is None:
        return default_prefix
    return str(Database.GUILDS.find_one({'_id': message.guild.id})['prefix'])


class MyBot(commands.Bot):
    def __init__(self):
        mentionable = discord.AllowedMentions(
            replied_user=False
        )

        intents = discord.Intents.all()
        super().__init__(
            command_prefix=self.__fetch_prefix,
            allowed_mentions=mentionable,
            intents=intents,
            help_command=None
        )

        cog_loader(self)

    @staticmethod
    def __fetch_prefix(bot: commands.Bot, message: discord.Message):
        return commands.when_mentioned_or(fetch_prefix(bot, message))(bot, message)

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = discord.utils.utcnow()

        await self.change_presence(activity=discord.Game(name=f'Toram | @mention_me'))
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


bot = MyBot()


@bot.event
async def on_message(message: discord.Message):
    """If the bot gets mentioned
    """
    if message.guild:
        cnt = message.content.split()  # the split message into list
        if cnt and message.author.bot is False and len(cnt) == 1:
            if re.match(f'<@!?{bot.user.id}>', cnt[0]):
                prefix = await bot.get_prefix(message)
                embed = discord.Embed(
                    description=f"Hello {message.author.mention}!\n`{prefix[2]}help` for more information")
                await message.channel.send(embed=embed)
    await bot.process_commands(message)


try:
    token = os.environ['TOKEN']
except KeyError:
    token = os.environ['TEST_TOKEN']

bot.run(token)
