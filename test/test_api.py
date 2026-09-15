import os
from pathlib import Path

os.environ["COOKBASE_DB_PATH"] = "/tmp/cookbase_test.db"

from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


def setup_module() -> None:
    db_path = Path(os.environ["COOKBASE_DB_PATH"])

    if db_path.exists():
        db_path.unlink()

    init_db()


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_inventory_item() -> None:
    response = client.post(
        "/api/ingredients",
        json={
            "name": "rice",
            "quantity": 500,
            "unit": "g",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "rice"
    assert data["quantity"] == 500
    assert data["unit"] == "g"


def test_create_recipe() -> None:
    response = client.post(
        "/api/recipes",
        json={
            "name": "Rice Bowl",
            "servings": 2,
            "instructions": "Cook everything.",
            "ingredients": [
                {
                    "ingredient_name": "rice",
                    "quantity": 200,
                    "unit": "g",
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Rice Bowl"


def test_recipe_matching() -> None:
    response = client.get("/api/matches")

    assert response.status_code == 200

    matches = response.json()

    assert len(matches) >= 1

    first_match = matches[0]

    assert "maximum_servings" in first_match
    assert "ingredients" in first_match


def test_invalid_unit() -> None:
    response = client.post(
        "/api/ingredients",
        json={
            "name": "water",
            "quantity": 2,
            "unit": "bucket",
        },
    )

    assert response.status_code == 422
