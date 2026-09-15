from __future__ import annotations

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "cookbase.db"


def get_db_path() -> Path:
    return Path(os.getenv("COOKBASE_DB_PATH", DEFAULT_DB_PATH))


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
            );

            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL UNIQUE,
                quantity REAL NOT NULL CHECK (quantity > 0),
                unit TEXT NOT NULL,
                FOREIGN KEY (ingredient_id)
                    REFERENCES ingredients(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                servings INTEGER NOT NULL CHECK (servings > 0),
                instructions TEXT NOT NULL DEFAULT ""
            );

            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL CHECK (quantity > 0),
                unit TEXT NOT NULL,
                UNIQUE(recipe_id, ingredient_id),
                FOREIGN KEY (recipe_id)
                    REFERENCES recipes(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (ingredient_id)
                    REFERENCES ingredients(id)
                    ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_recipe
            ON recipe_ingredients(recipe_id);

            CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_ingredient
            ON recipe_ingredients(ingredient_id);
            """
        )


def seed_demo_data() -> None:
    with get_connection() as connection:
        recipe_count = connection.execute(
            "SELECT COUNT(*) AS count FROM recipes"
        ).fetchone()["count"]

        inventory_count = connection.execute(
            "SELECT COUNT(*) AS count FROM inventory"
        ).fetchone()["count"]

        if recipe_count == 0:
            rice_id = _get_or_create_ingredient(connection, "rice")
            egg_id = _get_or_create_ingredient(connection, "egg")
            oil_id = _get_or_create_ingredient(connection, "cooking oil")

            recipe_cursor = connection.execute(
                """
                INSERT INTO recipes(name, servings, instructions)
                VALUES (?, ?, ?)
                """,
                (
                    "Simple Fried Rice",
                    2,
                    "Cook the rice, add egg, then stir-fry everything with oil.",
                ),
            )
            recipe_id = recipe_cursor.lastrowid

            connection.executemany(
                """
                INSERT INTO recipe_ingredients(
                    recipe_id,
                    ingredient_id,
                    quantity,
                    unit
                )
                VALUES (?, ?, ?, ?)
                """,
                [
                    (recipe_id, rice_id, 300, "g"),
                    (recipe_id, egg_id, 2, "pcs"),
                    (recipe_id, oil_id, 1, "tbsp"),
                ],
            )

        if inventory_count == 0:
            rice_id = _get_or_create_ingredient(connection, "rice")
            egg_id = _get_or_create_ingredient(connection, "egg")
            oil_id = _get_or_create_ingredient(connection, "cooking oil")

            connection.executemany(
                """
                INSERT INTO inventory(ingredient_id, quantity, unit)
                VALUES (?, ?, ?)
                """,
                [
                    (rice_id, 600, "g"),
                    (egg_id, 3, "pcs"),
                    (oil_id, 2, "tbsp"),
                ],
            )


def _get_or_create_ingredient(
    connection: sqlite3.Connection,
    name: str,
) -> int:
    normalized = name.strip().lower()

    row = connection.execute(
        "SELECT id FROM ingredients WHERE name = ? COLLATE NOCASE",
        (normalized,),
    ).fetchone()

    if row:
        return int(row["id"])

    cursor = connection.execute(
        "INSERT INTO ingredients(name) VALUES (?)",
        (normalized,),
    )
    return int(cursor.lastrowid)
