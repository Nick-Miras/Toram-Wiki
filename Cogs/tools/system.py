import discord
import pymongo.errors
from discord.ext import commands, tasks
from pymongo.results import DeleteResult
from pymongo.results import InsertManyResult

from Utils.dataclasses.guild import Guild
from database import get_mongodb_client, mongo_collection
from database.models import WhiskeyDatabase


#  TODO: Add Logging
class GuildDatabase:

    def __init__(self, collection: mongo_collection):
        self.collection = collection

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
        if guilds_not_added:
            GuildDatabase(collection=self.collection).add(guilds_not_added)

    def remove_invalid_guild_in_database(self, bot: commands.Bot):
        """This functions checks whether a guild in the database isn't a joined guild and removes them
        """
        added_that_are_not_exempted: list[int] = [guild['_id'] for guild in self.collection.find({'exempted': False})]

        # current joined guilds of the bot
        not_joined: list[int] = [guild.id for guild in bot.guilds if guild.id not in added_that_are_not_exempted]
        if not_joined:
            GuildDatabase(collection=self.collection).remove(not_joined)

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
        self.change_presence_every_minute.start()
        if self.bot.application_id == 876662819511218207:
            self.remove_invalid_guild_in_database(self.bot)
            self.add_not_added_guilds(self.bot)

    @tasks.loop(seconds=10)
    async def change_presence_every_minute(self):
        """changes the presence of the bot every minute with different description after every two minutes"""
        if self.bot.uptime.minute % 2 == 0:
            await self.bot.change_presence(activity=discord.Game(name=f'@me for help'))
        else:
            await self.bot.change_presence(activity=discord.Game(name=f'with {len(self.bot.guilds)} servers'))


async def setup(bot):
    await bot.add_cog(System(bot))
