from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecipeSummary(BaseModel):
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
        min_length=1,
        max_length=2000
    )

    @field_validator('description', mode='before')
    @classmethod
    def empty_str_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    model_config = ConfigDict(
        from_attributes=True,
        extra='forbid',
        str_strip_whitespace=True
    )


class Recipe(RecipeSummary):
    ingredients: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        min_length=1,
        max_length=50
    )
    steps: list[Annotated[str, Field(min_length=1, max_length=1000)]] = Field(
        min_length=1,
        max_length=30,
    )


class RecipeRecommendation(RecipeSummary):
    similarity: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )


class LikeResponse(BaseModel):
    liked: bool = Field(
        description='Indicates whether the recipe is currently favorited by the user'
    )

    model_config = ConfigDict(
        extra='forbid'
    )