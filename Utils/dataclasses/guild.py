from pydantic import BaseModel as PydanticBaseModel, Field


class Guild(PydanticBaseModel):
    id: int = Field(..., alias='_id')
    prefix: str = '.'
    exempted: bool = False
