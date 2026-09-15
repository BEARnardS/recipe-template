from __future__ import annotations

import math
from typing import Any

from .repositories import get_inventory_by_ingredient, get_recipe


UNIT_GROUPS = {
    "g": ("mass", 1.0),
    "kg": ("mass", 1000.0),
    "ml": ("volume", 1.0),
    "l": ("volume", 1000.0),
    "tsp": ("volume", 4.92892),
    "tbsp": ("volume", 14.7868),
    "cup": ("volume", 236.588),
    "pcs": ("count", 1.0),
    "piece": ("count", 1.0),
    "pieces": ("count", 1.0),
}


def convert_quantity(
    quantity: float,
    from_unit: str,
    to_unit: str,
) -> float | None:
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()

    if from_unit not in UNIT_GROUPS or to_unit not in UNIT_GROUPS:
        return None

    from_group, from_factor = UNIT_GROUPS[from_unit]
    to_group, to_factor = UNIT_GROUPS[to_unit]

    if from_group != to_group:
        return None

    base_quantity = quantity * from_factor
    return base_quantity / to_factor


def calculate_recipe_match(recipe_id: int) -> dict[str, Any] | None:
    recipe = get_recipe(recipe_id)

    if not recipe:
        return None

    inventory = get_inventory_by_ingredient()

    results = []
    ratios = []

    for ingredient in recipe["ingredients"]:
        name = ingredient["name"].strip().lower()
        required = float(ingredient["quantity"])
        required_unit = ingredient["unit"]

        inventory_item = inventory.get(name)

        if inventory_item is None:
            results.append(
                {
                    "name": ingredient["name"],
                    "required_quantity": required,
                    "required_unit": required_unit,
                    "available_quantity": 0,
                    "available_unit": None,
                    "status": "missing",
                    "deficit": required,
                    "deficit_unit": required_unit,
                    "ratio": 0,
                }
            )
            ratios.append(0)
            continue

        available_in_recipe_unit = convert_quantity(
            float(inventory_item["quantity"]),
            inventory_item["unit"],
            required_unit,
        )

        if available_in_recipe_unit is None:
            results.append(
                {
                    "name": ingredient["name"],
                    "required_quantity": required,
                    "required_unit": required_unit,
                    "available_quantity": float(inventory_item["quantity"]),
                    "available_unit": inventory_item["unit"],
                    "status": "incompatible_unit",
                    "deficit": None,
                    "deficit_unit": None,
                    "ratio": 0,
                }
            )
            ratios.append(0)
            continue

        ratio = available_in_recipe_unit / required
        deficit = max(required - available_in_recipe_unit, 0)

        if available_in_recipe_unit >= required:
            status = "available"
        else:
            status = "insufficient"

        results.append(
            {
                "name": ingredient["name"],
                "required_quantity": required,
                "required_unit": required_unit,
                "available_quantity": available_in_recipe_unit,
                "available_unit": required_unit,
                "status": status,
                "deficit": deficit,
                "deficit_unit": required_unit,
                "ratio": ratio,
            }
        )

        ratios.append(ratio)

    limiting_ratio = min(ratios) if ratios else 0
    maximum_servings = math.floor(
        limiting_ratio * recipe["servings"]
    )

    can_prepare = all(
        item["status"] == "available"
        for item in results
    )

    return {
        "recipe_id": recipe["id"],
        "recipe_name": recipe["name"],
        "recipe_servings": recipe["servings"],
        "can_prepare": can_prepare,
        "maximum_servings": maximum_servings,
        "limiting_ratio": round(limiting_ratio, 4),
        "ingredients": results,
    }


def calculate_all_matches() -> list[dict[str, Any]]:
    from .repositories import list_recipes

    matches = []

    for recipe in list_recipes():
        match = calculate_recipe_match(recipe["id"])

        if match:
            matches.append(match)

    return matches
