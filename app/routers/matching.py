from fastapi import APIRouter, HTTPException

from ..schemas import RecipeMatch
from ..services import (
    calculate_all_matches,
    calculate_recipe_match,
)

router = APIRouter(
    prefix="/api/matches",
    tags=["Matching"],
)


@router.get("", response_model=list[RecipeMatch])
def match_all_recipes() -> list[RecipeMatch]:
    return calculate_all_matches()


@router.get("/{recipe_id}", response_model=RecipeMatch)
def match_recipe(recipe_id: int) -> RecipeMatch:
    result = calculate_recipe_match(recipe_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found.",
        )

    return result
