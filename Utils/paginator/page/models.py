from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel as PydanticBaseModel, Field


class TreeInformation(PydanticBaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: Optional[str] = None
