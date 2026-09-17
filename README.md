# CookBase
.
A simple web-based cooking assistant for managing ingredient inventory, storing recipes, and determining what can be prepared with the ingredients currently available.

## Project Overview

CookBase solves a simple problem:

> "I have these ingredients. What can I make?"

Instead of manually checking recipes against a kitchen inventory, CookBase stores available ingredients and compares them against recipe requirements.

The application calculates:

- Available ingredients
- Missing ingredients
- Insufficient quantities
- Unit compatibility
- Maximum possible servings
- Whether the complete recipe can currently be prepared

CookBase is deliberately an MVP. It does not use AI, authentication, nutrition databases, social features, cloud services, or external APIs.

## Problem Statement

Home cooks often know what ingredients they have but do not know which recipes can be prepared without manually checking every requirement.

The core challenge is therefore an inventory-to-recipe matching problem:

1. Store current ingredients.
2. Store recipe requirements.
3. Compare required quantities with available quantities.
4. Identify constraints.
5. Calculate the maximum number of servings possible.

## Key Features

### Inventory Management

Users can:

- Add ingredients.
- Set quantities.
- Select units.
- Edit inventory items.
- Delete inventory items.
- View the current inventory.

### Recipe Management

Users can:

- Create recipes.
- Define base servings.
- Add recipe ingredients.
- Set required quantities.
- Add instructions.
- View stored recipes.

### Recipe Matching

CookBase compares inventory against every recipe.

For every recipe ingredient, the system reports:

- `available`
- `insufficient`
- `missing`
- `incompatible_unit`

The system also calculates the maximum number of servings possible.

## Matching Model

For a compatible ingredient:

```text
ratio = available_quantity / required_quantity
