import discord


class Models:

    @staticmethod
    def guild_document(guild_id: int) -> dict:
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

    @staticmethod
    def error_embed(message=None):
        """Embed for Error Messages

        Parameters
        -----------
        message: :class: `str`
            The error message to be sent.
        """
        embed = discord.Embed(
            description=message,
            color=ColorVar.error_red
        )
        embed.set_thumbnail(url=Images.exclamation)
        embed.set_author(name='Error!')
        return embed

    @staticmethod
    def success_embed(message=None):
        """Embed for Successful Processes or Command Invocations


        Parameters
        -----------
        message: :class: `str`
            The success message to be sent.
        """
        embed = discord.Embed(
            description=message,
            color=ColorVar.bright_green
        )
        embed.set_thumbnail(url=Images.successful)
        embed.set_author(name='Success!')
        return embed

    @staticmethod
    def notification(message=None):
        embed = discord.Embed(
            description=message,
            color=ColorVar.gold
        )
        embed.set_author(name='Notification!')
        embed.set_thumbnail(url=Images.notifications)
        return embed


class Images:
    notifications = "https://cdn.discordapp.com/attachments/432408793998163968/823831128967348224/1616487022293.png"
    successful = "https://cdn.discordapp.com/attachments/432408793998163968/805694947911008286/1612163017202.png"
    exclamation = "https://cdn.discordapp.com/attachments/432408793998163968/805694690879209482/error-flat.png"
    bank = "https://image.flaticon.com/icons/png/512/2830/2830284.png"
    reaffirmation = "https://image.flaticon.com/icons/png/512/2867/2867644.png"

    monocle = "https://cdn.discordapp.com/attachments/432408793998163968/787508055410868269/1607826945317.png"
    scroll = "https://cdn.discordapp.com/attachments/432408793998163968/740200163330621450/20200804_185612.jpg"


class ColorVar:
    dollar_bill = 0x85bb65
    gold = 0xffd700
    bright_green = 0x7fff00
    error_red = 0xcc0000
    blood_red = 0x880808
    blue_1 = 0x399cbd
