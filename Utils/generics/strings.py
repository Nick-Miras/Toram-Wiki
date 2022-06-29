import json
from enum import Enum
from typing import Type


class Grams:  # n word grams

    @staticmethod
    def ngrams(string):
        for i in range(1, len(string) + 1):
            yield string[0:i].lower()

    @staticmethod
    def gram(string, n: int):  # incremental
        """create grams of length n from string"""
        for i in range(len(string) - n + 1):
            yield string[i:i + n].lower()

    @classmethod
    def trigram(cls, string):
        return cls.gram(string, 3)


def remove_underscores(string: str) -> str:
    """replace underscores from a string with whitespace if it does not start with an underscore"""
    if string.startswith("_"):
        return string
    return string.replace("_", " ")


def strip_enclosing_parentheses(string: str) -> str:
    """strip enclosing parentheses from a string"""
    return string.strip("()")


def strip_enclosing_brackets(string: str) -> str:
    """strip enclosing brackets from a string"""
    return string.strip("[]")


def convert_to_bool(string: str) -> bool:
    """convert the string 'Yes' or 'No' to bool"""
    match string.lower():
        case 'yes':
            return True
        case 'no':
            return False


def convert_json_string_to_dict(string: str) -> dict:
    """convert a json string to a dictionary"""
    return json.loads(string)


def is_valid_enum_value(string: str, enum: Type[Enum]) -> bool:
    """check if a string is a valid enum value"""
    return string in [member.value for member in enum.__members__.values()]
