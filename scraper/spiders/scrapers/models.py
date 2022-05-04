from typing import Type, Optional

from pydantic import BaseModel as PydanticBaseModel, HttpUrl, Field, validator

from Utils.types import Empty
from scraper.spiders.converters import IDataclassFactory
from scraper.spiders.parsers.abc import BaseParser
from scraper.spiders.parsers.container_paths import ContainerPaths


class ScraperInformation(PydanticBaseModel):
    """Information that will be used and required by the scraper"""
    url: HttpUrl
    parser: Type[BaseParser] = Field(..., allow_mutation=False)  # uninitialized object
    next_page: bool  # if scraper should access the next page
    container_path: Type[ContainerPaths] = Field(Empty, allow_mutation=False)  # uninitialized object
    converter: Optional[IDataclassFactory] = Field(None, allow_mutation=False)

    @validator('container_path', pre=True, always=True)
    def set_container_path(cls, _, values):
        return values['parser'].container_path

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
