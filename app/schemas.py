from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


SUPPORTED_UNITS = {
    "g",
    "kg",
    "ml",
    "l",
    "tsp",
    "tbsp",
    "cup",
    "pcs",
    "piece",
    "pieces",
}


class IngredientInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Ingredient name cannot be empty.")

        return value

    @field_validator("unit")
    @classmethod
    def clean_unit(cls, value: str) -> str:
        value = value.strip().lower()

        if value not in SUPPORTED_UNITS:
            raise ValueError(
                f"Unsupported unit '{value}'. "
                f"Supported units: {', '.join(sorted(SUPPORTED_UNITS))}"
            )

        return value


class IngredientUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Ingredient name cannot be empty.")

        return value

    @field_validator("unit")
    @classmethod
    def clean_unit(cls, value: str) -> str:
        value = value.strip().lower()

        if value not in SUPPORTED_UNITS:
            raise ValueError(
                f"Unsupported unit '{value}'. "
                f"Supported units: {', '.join(sorted(SUPPORTED_UNITS))}"
            )

        return value


class RecipeIngredientInput(BaseModel):
    ingredient_name: str = Field(min_length=1, max_length=100)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)

    @field_validator("ingredient_name")
    @classmethod
    def clean_ingredient_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Ingredient name cannot be empty.")

        return value

    @field_validator("unit")
    @classmethod
    def clean_unit(cls, value: str) -> str:
        value = value.strip().lower()

        if value not in SUPPORTED_UNITS:
            raise ValueError(
                f"Unsupported unit '{value}'. "
                f"Supported units: {', '.join(sorted(SUPPORTED_UNITS))}"
            )

        return value


class RecipeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    servings: int = Field(gt=0, le=10000)
    instructions: str = Field(default="", max_length=10000)
    ingredients: list[RecipeIngredientInput] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Recipe name cannot be empty.")

        return value


class RecipeUpdate(RecipeCreate):
    pass


class InventoryItem(BaseModel):
    id: int
    ingredient_id: int
    name: str
    quantity: float
    unit: str


class RecipeIngredient(BaseModel):
    ingredient_id: int
    name: str
    quantity: float
    unit: str


class Recipe(BaseModel):
    id: int
    name: str
    servings: int
    instructions: str
    ingredients: list[RecipeIngredient]


class MatchIngredient(BaseModel):
    name: str
    required_quantity: float
    required_unit: str
    available_quantity: float
    available_unit: str | None
    status: str
    deficit: float | None
    deficit_unit: str | None
    ratio: float


class RecipeMatch(BaseModel):
    recipe_id: int
    recipe_name: str
    recipe_servings: int
    can_prepare: bool
    maximum_servings: int
    limiting_ratio: float
    ingredients: list[MatchIngredient]
