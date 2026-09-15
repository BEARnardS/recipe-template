from fastapi import APIRouter, HTTPException, status

from ..repositories import (
    delete_inventory,
    get_inventory_item,
    list_inventory,
    update_inventory,
    upsert_inventory,
)
from ..schemas import IngredientInput, IngredientUpdate, InventoryItem

router = APIRouter(
    prefix="/api/ingredients",
    tags=["Inventory"],
)


@router.get("", response_model=list[InventoryItem])
def get_inventory() -> list[InventoryItem]:
    return list_inventory()


@router.post(
    "",
    response_model=InventoryItem,
    status_code=status.HTTP_201_CREATED,
)
def add_inventory_item(data: IngredientInput) -> InventoryItem:
    return upsert_inventory(
        name=data.name,
        quantity=data.quantity,
        unit=data.unit,
    )


@router.get("/{item_id}", response_model=InventoryItem)
def get_inventory_by_id(item_id: int) -> InventoryItem:
    item = get_inventory_item(item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory item not found.",
        )

    return item


@router.put("/{item_id}", response_model=InventoryItem)
def edit_inventory_item(
    item_id: int,
    data: IngredientUpdate,
) -> InventoryItem:
    try:
        item = update_inventory(
            item_id=item_id,
            name=data.name,
            quantity=data.quantity,
            unit=data.unit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory item not found.",
        )

    return item


@router.delete("/{item_id}")
def remove_inventory_item(item_id: int) -> dict[str, str]:
    deleted = delete_inventory(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Inventory item not found.",
        )

    return {"message": "Inventory item deleted."}
