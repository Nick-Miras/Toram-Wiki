import discord
from bson import ObjectId, CodecOptions
from bson.codec_options import TypeRegistry
from discord.ext import commands

from Cogs.exceptions import CmdError
from Utils.dataclasses.paginator import PageType, InformationPage
from Utils.generics.discord import SuccessEmbed
from Utils.generics.strings import is_valid_enum_value, convert_json_string_to_dict
from database import get_mongodb_client, mongo_collection
from database.codec import DiscordEmbedCodec
from database.models import WhiskeyDatabase


class PageBuilder:

    def __init__(self, data: InformationPage):
        self.data = data

    def push_to_database(self, collection: mongo_collection) -> None:
        collection.insert_one(self.data.dict(by_alias=True))

    def remove_from_database(self, collection: mongo_collection) -> None:
        collection.delete_one({'_id': self.data.id})


def get_pages_collection(page_type: str) -> mongo_collection:
    return WhiskeyDatabase(get_mongodb_client()).pages.get_collection(
        f'pages.{page_type}', codec_options=CodecOptions(type_registry=TypeRegistry([DiscordEmbedCodec()]))
    )


class OwnerCommands(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.group(invoke_without_command=True, name='page')
    @commands.is_owner()
    async def page_command(self, ctx: commands.Context):
        await ctx.send('This is a page command')

    @page_command.command(name='add')
    @commands.is_owner()
    async def page_add_command(self, ctx: commands.Context, page_type: str, parent_id: str, *, embed_json: str):
        if is_valid_enum_value(page_type, PageType) is False:
            raise CmdError(f'{page_type} is not a valid page type')

        embed = discord.Embed.from_dict(convert_json_string_to_dict(embed_json))
        PageBuilder(
            InformationPage(
                parent=ObjectId(parent_id),
                embed=embed
            )
        ).push_to_database(get_pages_collection(page_type))
        await ctx.send(embed=SuccessEmbed.display('Successfully Added Page!'), ephemeral=True)
        await ctx.send(embed=embed, ephemeral=True)

    @page_command.command(name='remove')
    @commands.is_owner()
    async def page_remove_command(self, ctx: commands.Context, page_type: str, page_id: str):
        if is_valid_enum_value(page_type, PageType) is False:
            raise CmdError(f'{page_type} is not a valid page type')


async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))
