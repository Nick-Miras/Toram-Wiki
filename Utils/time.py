"""
This is the class that contains the timezone related functions

Note:
    Due to changes in discord.py 2.0. For Naive datetime objects that are passed around discord.py objects.
    discord.utils.utcnow() must be used instead
"""
from datetime import datetime
from datetime import timezone as tz
from zoneinfo import ZoneInfo
import pytz
from typing import Union
from discord.ext import commands
from .errors import Error
import discord

fmt = '%Y-%m-%d %I:%M %p'  # 2012-12-21 01:50 PM

timezone_picker = '[link](https://kevinnovak.github.io/Time-Zone-Picker/)'
utcnow = discord.utils.utcnow


class TimeConverter(commands.Converter):

    async def convert(self, ctx, argument):
        # converts a time string into a datetime object without timezone information
        if ToTime.valid_time(argument) is False:
            error = f'{argument} is not a valid string format\nValid Format Example: `2012-12-21 01:50 PM`'
            raise Error(error, embed=True)
        return ToTime.time_to_datetime(argument)


class TimeError(Exception):
    pass


class InvalidTimeFormat(TimeError):
    def __init__(self, time: str):  # TODO: Argument is subject for removal
        self.arg = time
        super().__init__(f'{time} is not a valid string format\nValid Format Example: `2012-12-21 01:50 PM`')


class InvalidTimezone(TimeError):
    def __init__(self, timezone: str):  # TODO: Argument is subject for removal
        self.arg = timezone
        super().__init__(f'{timezone} is not a valid timezone\nValid Timezones: {timezone_picker}')


class Empty:  # TODO: Subject for removal
    def __bool__(self):
        return False

    def __repr__(self):
        return 'Empty'

    def __len__(self):
        return 0


class TimeProxy:
    def __init__(self, layer):
        self.__dict__.update(layer)

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return 'EmbedProxy(%s)' % ', '.join(('%s=%r' % (k, v) for k, v in self.__dict__.items() if not k.startswith('_')))

    def __getattr__(self, attr):
        return Empty


class ToTime:
    """
    Attributes
    -----------
    time: Union[:class:`str`, :class:`datetime.datetime`]
        This is the time argument
    timezone: :class:`str`
        If this is left blank then the timezone will default to UTC
    """

    __slots__ = ('type', '_time', '_timezone', '_local', '_utc', '_to_timezone')
    # is localized attr is not added since we won't ever use it

    def __init__(self, *, time: Union[str, datetime], timezone='UTC', to_timezone='UTC'):
        self.to_timezone = to_timezone
        self.timezone = timezone
        # If `timezone` is not utc, this will be the timezone the `timezone` will be converted into
        self.time = time

    @property
    def timezone(self):
        return self._timezone

    @timezone.setter
    def timezone(self, timezone):
        if timezone not in pytz.all_timezones_set:
            raise InvalidTimezone(timezone)
        self._timezone = timezone

    @property
    def to_timezone(self):
        return self._to_timezone

    @to_timezone.setter
    def to_timezone(self, timezone):
        if timezone not in pytz.all_timezones_set:
            raise InvalidTimezone(timezone)
        self._to_timezone = timezone

    @property
    def time(self) -> Union[str, datetime]:
        return self._time

    @time.setter
    def time(self, time):
        if type(time) not in [datetime, str]:
            raise Exception(f'{time} is not Union[str, datetime]')

        if isinstance(time, datetime):
            self.type = datetime
            self._time: datetime = time.replace(tzinfo=ZoneInfo(self.timezone))

        if isinstance(time, str):
            if self.valid_time(time) is False:
                raise InvalidTimeFormat(time)
            self.type = str
            self._time: str = time

    @property
    def datetimes(self):
        """Returns the datetime object of self.time
        """
        if self.type is str:
            datetime_object = datetime.strptime(self.time, fmt)  # the datetime object
            return datetime_object.replace(tzinfo=ZoneInfo(self.timezone))
        return self.time

    @property
    def times(self):
        """Returns the `time` string of self.time
        """
        if self.type is datetime:
            return self.time.strftime(fmt)
        return self.time

    @staticmethod
    def valid_time(time: str):
        """This functions validates a time string

        :param time: 'string' '%Y-%m-%d %I:%M %p' Example: 2012-12-21 01:50 PM
        """
        try:
            datetime.strptime(time, fmt)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def time_to_datetime(time):
        """
        This turns a string into a datetime object.

        :param time: 'string' '%Y-%m-%d %I:%M %p' Example: 2012-12-21 01:50 PM
        :return: datetime.datetime
        """

        datetime_object = datetime.strptime(time, fmt)  # the datetime object
        return datetime_object

    @staticmethod
    def datetime_to_time(datetime: datetime):
        """

        :param datetime: `datetime` object
        :return: 'string' '%Y-%m-%d %I:%M %p' Example: 2012-12-21 01:50 PM
        """
        return datetime.strftime(fmt)

    @property
    def local(self):
        self.set_local()
        return TimeProxy(getattr(self, '_local', {}))

    def set_local(self):  # from utc to local or local to local
        local_datetime = self.datetimes.astimezone(ZoneInfo(self._to_timezone))
        local_string = local_datetime.strftime(fmt)

        self._local = {
            'time': local_string,
            'datetime': local_datetime
        }

        return self

    @property
    def utc(self):
        self.set_utc()
        return TimeProxy(getattr(self, '_utc', {}))

    def set_utc(self):
        utc_datetime = self.datetimes.astimezone(tz.utc)  # this is the datetime OBJECT in utc
        utc_string = utc_datetime.strftime(fmt)

        self._utc = {
            'time': utc_string,
            'datetime': utc_datetime
        }

        return self

    def has_pass(self):
        """This functions checks if self.time is already in the past
        """
        if utcnow() > self.utc.datetime:
            return True  # time is already in the past
        return


class Time:
    """
    Link to timezone picker: https://kevinnovak.github.io/Time-Zone-Picker/
    """
    _utc = pytz.utc
    _times = utcnow()
    now = f"{_times.strftime(fmt)}UTC"

    @staticmethod
    async def get_timezone(ctx):
        """
        :return: ctx.guild's Timezone
        """
        timezone = Database.GUILDS.find_one({'_id': ctx.guild.id})['timezone']
        return timezone

    @staticmethod
    def time_to_datetime(time):
        """
        This turns a string into a datetime object.

        :param time: 'string' '%Y-%m-%d %I:%M %p' Example: 2012-12-21 01:50 PM
        :return: datetime.datetime
        """

        datetime_object = datetime.strptime(time, fmt)  # the datetime object
        return datetime_object

    @classmethod
    def to_utc(cls, time, timezone):
        """

        :param time: 'string' '%Y-%m-%d %I:%M %p' Example: 2012-12-21 01:50 PM
        :param timezone: Discord Server Timezone
        :return: 'string' in utc time
        """
        datetime_object = cls.time_to_datetime(time)
        local_timezone = pytz.timezone(timezone)

        local_moment = local_timezone.localize(datetime_object, is_dst=None)

        to_utc = local_moment.astimezone(pytz.utc)  # this is the datetime OBJECT in utc
        utc = to_utc.strftime(fmt)
        return utc  # converted time to utc Example: 2012-12-21 01:50 PM

    @staticmethod
    def datetime_to_time(datetime: datetime):
        """

        :param datetime: `datetime` object
        :return: 'string' '%Y-%m-%d %I:%M %p' Example: 2012-12-21 01:50 PM
        """
        return datetime.strftime(fmt)

    @classmethod
    def to_local(cls, time, timezone):
        """
        This functions converts a time 'string' to a localized datetime object.

        :param time: 'string' '%Y-%m-%d %I:%M %p' Example: 2012-12-21 01:50 PM
        :param timezone: Discord Server Timezone
        :return: localized datetime object
        """
        datetime_object = cls.time_to_datetime(time)
        local_timezone = pytz.timezone(timezone)

        local_datetime = local_timezone.localize(datetime_object)
        return local_datetime

    @classmethod
    def to_local_time(cls, time, timezone):
        """
        This functions converts a time 'string' to a localized time string.

        :param time: 'string' '%Y-%m-%d %I:%M %p' Example: 2012-12-21 01:50 PM
        :param timezone: Discord Server Timezone
        :return: localized time string.
        """
        datetime_object = time
        local_timezone = pytz.timezone(timezone)

        local_datetime = local_timezone.localize(datetime_object)
        time = cls.datetime_to_time(local_datetime)
        return time

    @staticmethod
    def valid_time(time):
        """This functions validates a time string

        :param time: 'string' '%Y-%m-%d %I:%M %p' Example: 2012-12-21 01:50 PM
        """
        try:
            datetime.strptime(time, fmt)
        except ValueError:
            return False
        else:
            return True

    @classmethod
    def has_pass(cls, time: str, timezone):
        """This functions checks if a time is already in the past

        :param time:
            `str` '%Y-%m-%d %I:%M %p' Example: 2012-12-21 01:50 PM or
            `datetime` object
        :param timezone:
            `str` The timezone
        :return:
            If time has already has pass then return `True`
        """
        # Turns it into a utc object
        time = cls.time_to_datetime(cls.to_utc(time, timezone))
        if utcnow() > time:
            return True
        return
