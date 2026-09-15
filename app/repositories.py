from __future__ import annotations

import sqlite3
from typing import Any

from .database import get_connection


def list_inventory() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                inventory.id,
                inventory.ingredient_id,
                ingredients.name,
                inventory.quantity,
                inventory.unit
            FROM inventory
            JOIN ingredients
                ON ingredients.id = inventory.ingredient_id
            ORDER BY ingredients.name
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_inventory_item(item_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                inventory.id,
                inventory.ingredient_id,
                ingredients.name,
                inventory.quantity,
                inventory.unit
            FROM inventory
            JOIN ingredients
                ON ingredients.id = inventory.ingredient_id
            WHERE inventory.id = ?
            """,
            (item_id,),
        ).fetchone()

    return dict(row) if row else None


def upsert_inventory(
    name: str,
    quantity: float,
    unit: str,
) -> dict[str, Any]:
    normalized_name = name.strip().lower()

    with get_connection() as connection:
        ingredient = connection.execute(
            """
            SELECT id
            FROM ingredients
            WHERE name = ? COLLATE NOCASE
            """,
            (normalized_name,),
        ).fetchone()

        if ingredient:
            ingredient_id = int(ingredient["id"])
        else:
            cursor = connection.execute(
                "INSERT INTO ingredients(name) VALUES (?)",
                (normalized_name,),
            )
            ingredient_id = int(cursor.lastrowid)

        existing = connection.execute(
            """
            SELECT id
            FROM inventory
            WHERE ingredient_id = ?
            """,
            (ingredient_id,),
        ).fetchone()

        if existing:
            connection.execute(
                """
                UPDATE inventory
                SET quantity = ?, unit = ?
                WHERE id = ?
                """,
                (quantity, unit, existing["id"]),
            )
            item_id = int(existing["id"])
        else:
            cursor = connection.execute(
                """
                INSERT INTO inventory(ingredient_id, quantity, unit)
                VALUES (?, ?, ?)
                """,
                (ingredient_id, quantity, unit),
            )
            item_id = int(cursor.lastrowid)

    return get_inventory_item(item_id)


def update_inventory(
    item_id: int,
    name: str,
    quantity: float,
    unit: str,
) -> dict[str, Any] | None:
    normalized_name = name.strip().lower()

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT ingredient_id
            FROM inventory
            WHERE id = ?
            """,
            (item_id,),
        ).fetchone()

        if not current:
            return None

        ingredient_id = int(current["ingredient_id"])

        name_conflict = connection.execute(
            """
            SELECT id
            FROM ingredients
            WHERE name = ? COLLATE NOCASE
              AND id != ?
            """,
            (normalized_name, ingredient_id),
        ).fetchone()

        if name_conflict:
            conflict_ingredient_id = int(name_conflict["id"])

            inventory_conflict = connection.execute(
                """
                SELECT id
                FROM inventory
                WHERE ingredient_id = ?
                  AND id != ?
                """,
                (conflict_ingredient_id, item_id),
            ).fetchone()

            if inventory_conflict:
                raise ValueError(
                    "Another inventory item already uses that ingredient name."
                )

            connection.execute(
                """
                UPDATE inventory
                SET ingredient_id = ?, quantity = ?, unit = ?
                WHERE id = ?
                """,
                (
                    conflict_ingredient_id,
                    quantity,
                    unit,
                    item_id,
                ),
            )
        else:
            connection.execute(
                """
                UPDATE ingredients
                SET name = ?
                WHERE id = ?
                """,
                (normalized_name, ingredient_id),
            )

            connection.execute(
                """
                UPDATE inventory
                SET quantity = ?, unit = ?
                WHERE id = ?
                """,
                (quantity, unit, item_id),
            )

    return get_inventory_item(item_id)


def delete_inventory(item_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM inventory WHERE id = ?",
            (item_id,),
        )

    return cursor.rowcount > 0


def list_recipes() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, servings, instructions
            FROM recipes
            ORDER BY name
            """
        ).fetchall()

    recipes = []

    for row in rows:
        recipe = dict(row)
        recipe["ingredients"] = _get_recipe_ingredients(
            connection=None,
            recipe_id=recipe["id"],
        )
        recipes.append(recipe)

    return recipes


def get_recipe(recipe_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, servings, instructions
            FROM recipes
            WHERE id = ?
            """,
            (recipe_id,),
        ).fetchone()

        if not row:
            return None

        recipe = dict(row)
        recipe["ingredients"] = _get_recipe_ingredients(
            connection,
            recipe_id,
        )
        return recipe


def _get_recipe_ingredients(
    connection: sqlite3.Connection | None,
    recipe_id: int,
) -> list[dict[str, Any]]:
    own_connection = connection is None

    if own_connection:
        connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                recipe_ingredients.ingredient_id,
                ingredients.name,
                recipe_ingredients.quantity,
                recipe_ingredients.unit
            FROM recipe_ingredients
            JOIN ingredients
                ON ingredients.id = recipe_ingredients.ingredient_id
            WHERE recipe_ingredients.recipe_id = ?
            ORDER BY ingredients.name
            """,
            (recipe_id,),
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        if own_connection:
            connection.close()


def create_recipe(
    name: str,
    servings: int,
    instructions: str,
    ingredients: list[dict[str, Any]],
) -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO recipes(name, servings, instructions)
            VALUES (?, ?, ?)
            """,
            (name.strip(), servings, instructions.strip()),
        )
        recipe_id = int(cursor.lastrowid)

        for ingredient in ingredients:
            ingredient_id = _get_or_create_ingredient(
                connection,
                ingredient["ingredient_name"],
            )

            connection.execute(
                """
                INSERT INTO recipe_ingredients(
                    recipe_id,
                    ingredient_id,
                    quantity,
                    unit
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    recipe_id,
                    ingredient_id,
                    ingredient["quantity"],
                    ingredient["unit"],
                ),
            )

    return get_recipe(recipe_id)


def update_recipe(
    recipe_id: int,
    name: str,
    servings: int,
    instructions: str,
    ingredients: list[dict[str, Any]],
) -> dict[str, Any] | None:
    with get_connection() as connection:
        current = connection.execute(
            "SELECT id FROM recipes WHERE id = ?",
            (recipe_id,),
        ).fetchone()

        if not current:
            return None

        connection.execute(
            """
            UPDATE recipes
            SET name = ?, servings = ?, instructions = ?
            WHERE id = ?
            """,
            (
                name.strip(),
                servings,
                instructions.strip(),
                recipe_id,
            ),
        )

        connection.execute(
            "DELETE FROM recipe_ingredients WHERE recipe_id = ?",
            (recipe_id,),
        )

        for ingredient in ingredients:
            ingredient_id = _get_or_create_ingredient(
                connection,
                ingredient["ingredient_name"],
            )

            connection.execute(
                """
                INSERT INTO recipe_ingredients(
                    recipe_id,
                    ingredient_id,
                    quantity,
                    unit
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    recipe_id,
                    ingredient_id,
                    ingredient["quantity"],
                    ingredient["unit"],
                ),
            )

    return get_recipe(recipe_id)


def delete_recipe(recipe_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM recipes WHERE id = ?",
            (recipe_id,),
        )

    return cursor.rowcount > 0


def get_inventory_by_ingredient() -> dict[str, dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                ingredients.name,
                inventory.quantity,
                inventory.unit
            FROM inventory
            JOIN ingredients
                ON ingredients.id = inventory.ingredient_id
            """
        ).fetchall()

    return {
        row["name"].strip().lower(): dict(row)
        for row in rows
    }


def _get_or_create_ingredient(
    connection: sqlite3.Connection,
    name: str,
) -> int:
    normalized_name = name.strip().lower()

    row = connection.execute(
        """
        SELECT id
        FROM ingredients
        WHERE name = ? COLLATE NOCASE
        """,
        (normalized_name,),
    ).fetchone()

    if row:
        return int(row["id"])

    cursor = connection.execute(
        "INSERT INTO ingredients(name) VALUES (?)",
        (normalized_name,),
    )

    return int(cursor.lastrowid)
