import discord
from discord.ext import commands
import re
import os
from Utils import global_dict
from Utils.variables import Models
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

    @staticmethod
    async def add_guilds(bot: commands.Bot):
        # TODO: Change this function to delete guilds db objects
        #  that don't exist in the joined guilds of the bot
        """This function checks if a guild hasn't been added to the database yet
        """
        # a list of Guild ID's that have already been added
        already_added: list[int] = [guild['_id'] for guild in Database.GUILDS.find()]

        not_added_to_database: list[discord.Guild] = [guild for guild in bot.guilds if guild.id not in already_added]
        for guild in not_added_to_database:
            document = Models.guild_document(guild.id)
            Database.GUILDS.insert_one(document)
            print(f"Added: {guild.id}")

    @staticmethod
    async def remove_guilds(bot: commands.Bot):
        # TODO: Change this function to delete guilds db objects
        #  that don't exist in the joined guilds of the bot
        """This functions checks whether a guild in the database isn't a joined guild
        """
        # The exempted guilds that the bot shouldn't delete from the database
        exempted_guilds = (426956449860812818, 846204712796553246,)
        added: list[int] = [guild['_id'] for guild in Database.GUILDS.find()]

        # current joined guilds of the bot
        joined: list[int] = [guild.id for guild in bot.guilds]
        not_joined: list[int] = [guild_id for guild_id in added if guild_id not in joined]

        for ids in not_joined:
            if ids in exempted_guilds:
                print(f'Exempted: {ids}')
                continue
            Database.GUILDS.delete_one({'_id': ids})
            print(f"Removed: {ids}")

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = discord.utils.utcnow()

        await self.change_presence(activity=discord.Game(name=f'Toram | @mention_me'))
        await self.add_guilds(self)
        await self.remove_guilds(self)
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_guild_join(self, guild):
        document = Models.guild_document(guild.id)
        Database.GUILDS.insert_one(document)

    async def on_guild_remove(self, guild):
        Database.GUILDS.delete_one({"_id": guild.id})


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
                embed = discord.Embed(description=f"Hello {message.author.mention}!\n`{prefix[2]}help` for more information")
                await message.channel.send(embed=embed)
    await bot.process_commands(message)


try:
    token = os.environ['TOKEN']
except KeyError:
    token = os.environ['TEST_TOKEN']

bot.run(token)
