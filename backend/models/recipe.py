from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Recipe(BaseModel):
    id: int
    name: str = Field(
        min_length=3,
        max_length=150
    )
    minutes: int | None = Field(
        default=None,
        ge=1,
        le=4320
    )
    description: str | None = Field(
        default=None,
        max_length=2000
    )
    ingredients: list[Annotated[str, Field(min_length=3, max_length=100)]] = Field(
        default_factory=list,
        min_length=3,
        max_length=50
    )
    steps: list[Annotated[str, Field(min_length=3, max_length=1000)]] = Field(
        default_factory=list,
        min_length=1,
        max_length=30,
    )

    model_config = ConfigDict(
        from_attributes=True,
        extra='forbid',
        str_strip_whitespace=True
    )