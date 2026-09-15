from fastapi import APIRouter, HTTPException, status

from ..repositories import (
    create_recipe,
    delete_recipe,
    get_recipe,
    list_recipes,
    update_recipe,
)
from ..schemas import Recipe, RecipeCreate, RecipeUpdate

router = APIRouter(
    prefix="/api/recipes",
    tags=["Recipes"],
)


def _recipe_payload(data: RecipeCreate | RecipeUpdate) -> dict:
    ingredient_names = [
        ingredient.ingredient_name.strip().lower()
        for ingredient in data.ingredients
    ]

    if len(ingredient_names) != len(set(ingredient_names)):
        raise HTTPException(
            status_code=422,
            detail="Recipe ingredients must be unique.",
        )

    return {
        "name": data.name,
        "servings": data.servings,
        "instructions": data.instructions,
        "ingredients": [
            ingredient.model_dump()
            for ingredient in data.ingredients
        ],
    }


@router.get("", response_model=list[Recipe])
def get_recipes() -> list[Recipe]:
    return list_recipes()


@router.post(
    "",
    response_model=Recipe,
    status_code=status.HTTP_201_CREATED,
)
def add_recipe(data: RecipeCreate) -> Recipe:
    payload = _recipe_payload(data)

    return create_recipe(**payload)


@router.get("/{recipe_id}", response_model=Recipe)
def get_recipe_by_id(recipe_id: int) -> Recipe:
    recipe = get_recipe(recipe_id)

    if recipe is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found.",
        )

    return recipe


@router.put("/{recipe_id}", response_model=Recipe)
def edit_recipe(
    recipe_id: int,
    data: RecipeUpdate,
) -> Recipe:
    payload = _recipe_payload(data)

    recipe = update_recipe(
        recipe_id=recipe_id,
        **payload,
    )

    if recipe is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found.",
        )

    return recipe


@router.delete("/{recipe_id}")
def remove_recipe(recipe_id: int) -> dict[str, str]:
    deleted = delete_recipe(recipe_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found.",
        )

    return {"message": "Recipe deleted."}
