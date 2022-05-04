import discord
import pymongo.errors
from discord.ext import commands
from pymongo.results import DeleteResult
from pymongo.results import InsertManyResult

from Utils.dataclasses.guild import Guild
from database import get_mongodb_client, mongo_collection
from database.models import WhiskeyDatabase


#  TODO: Add Logging
class GuildDatabase:

    def __init__(self):
        self.collection = WhiskeyDatabase(get_mongodb_client()).discord_guilds

    def add(self, guilds: list[Guild]) -> InsertManyResult:
        return self.collection.insert_many([guild.dict(by_alias=True) for guild in guilds])

    def remove(self, guild_ids: list[int]) -> DeleteResult:
        return self.collection.delete_many({'_id': {'$in': guild_ids}})


class System(commands.Cog, name='system'):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.collection: mongo_collection = WhiskeyDatabase(get_mongodb_client()).discord_guilds

    def add_not_added_guilds(self, bot: commands.Bot):
        guilds_not_added: list[Guild] = [
            Guild(_id=guild.id) for guild in bot.guilds if self.collection.count_documents({'_id': guild.id}) == 0
        ]
        GuildDatabase().add(guilds_not_added)

    def remove_invalid_guild_in_database(self, bot: commands.Bot):
        """This functions checks whether a guild in the database isn't a joined guild and removes them
        """
        added_that_are_not_exempted: list[int] = [guild['_id'] for guild in self.collection.find({'exempted': False})]

        # current joined guilds of the bot
        not_joined: list[int] = [guild.id for guild in bot.guilds if guild.id not in added_that_are_not_exempted]
        GuildDatabase().remove(not_joined)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        try:
            self.collection.insert_one(Guild(_id=guild.id).dict(by_alias=True))
        except pymongo.errors.DuplicateKeyError:
            pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.collection.delete_one({"_id": guild.id})

    @commands.Cog.listener()
    async def on_ready(self):
        self.remove_invalid_guild_in_database(self.bot)
        self.add_not_added_guilds(self.bot)


async def setup(bot):
    await bot.add_cog(System(bot))
