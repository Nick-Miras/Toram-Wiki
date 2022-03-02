import discord
import pymongo.errors
from discord.ext import commands

from Utils.database import Database


def get_guild_document(guild_id: int) -> dict:
    """
    This function returns the database document for initializing new Discord Servers that were added

    :param guild_id: :class: `int` This is the id of the guild
    """
    assert isinstance(guild_id, int)
    document = {'_id': guild_id,
                'prefix': '.',
                'exempted': False
                }
    return document


# TODO: Remove PRINT Statements
class System(commands.Cog, name='system'):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @staticmethod
    async def add_guilds(bot: commands.Bot):
        """This function checks if a guild hasn't been added to the database yet
        """
        # a list of Guild ID's that have already been added
        already_added: list[int] = [guild['_id'] for guild in Database.GUILDS.find()]

        not_added_to_database: list[discord.Guild] = [guild for guild in bot.guilds if guild.id not in already_added]
        for guild in not_added_to_database:
            Database.GUILDS.insert_one(get_guild_document(guild.id))
            print(f"Added: {guild.id}")

    @staticmethod
    async def remove_guilds(bot: commands.Bot):
        """This functions checks whether a guild in the database isn't a joined guild
        """
        # The exempted guilds that the bot shouldn't delete from the database
        exempted_guilds = [guild['_id'] for guild in Database.GUILDS.find({'exempted': True})]
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

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        try:
            document = get_guild_document(guild.id)
            Database.GUILDS.insert_one(document)
        except pymongo.errors.DuplicateKeyError:
            pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        Database.GUILDS.delete_one({"_id": guild.id})

    @commands.Cog.listener()
    async def on_ready(self):
        await self.remove_guilds(self.bot)
        await self.add_guilds(self.bot)


def setup(bot):
    bot.add_cog(System(bot))
