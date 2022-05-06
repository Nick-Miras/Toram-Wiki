from typing import Type

from pydantic import BaseModel as PydanticBaseModel, BaseConfig, Extra

from scraper.spiders.parsers.models import ParserResults, ParserResultWrapper


class WikiBaseModel(PydanticBaseModel):
    pass


class WikiBaseConfig(BaseConfig):
    arbitrary_types_allowed = True
    allow_mutation = False
    extra = Extra.ignore
    use_enum_values = True


def dataclass_factory(item: ParserResultWrapper, model: Type[WikiBaseModel]) -> WikiBaseModel:
    """builder for :class:`PydanticBaseModel`"""
    data = {}
    for result in item['result']:
        result = ParserResults.parse_obj(result)
        data.update({result.parser['name']: result.result})

    return model.parse_obj(data)
