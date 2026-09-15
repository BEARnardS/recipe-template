const UNIT_OPTIONS = [
    "g",
    "kg",
    "ml",
    "l",
    "tsp",
    "tbsp",
    "cup",
    "pcs"
];

const inventoryForm = document.getElementById("inventory-form");
const recipeForm = document.getElementById("recipe-form");
const recipeIngredientsContainer =
    document.getElementById("recipe-ingredients");
const inventoryTable =
    document.getElementById("inventory-table");
const recipeResults =
    document.getElementById("recipe-results");
const toast = document.getElementById("toast");

document
    .getElementById("add-recipe-ingredient")
    .addEventListener("click", () => {
        addRecipeIngredientRow();
    });

document
    .getElementById("refresh-matches")
    .addEventListener("click", loadDashboard);

inventoryForm.addEventListener("submit", addInventory);
recipeForm.addEventListener("submit", createRecipe);

addRecipeIngredientRow();

loadDashboard();


async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        },
        ...options
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
        const detail =
            data?.detail ||
            `Request failed with status ${response.status}.`;

        throw new Error(detail);
    }

    return data;
}


async function loadDashboard() {
    try {
        const [inventory, recipes, matches] = await Promise.all([
            apiRequest("/api/ingredients"),
            apiRequest("/api/recipes"),
            apiRequest("/api/matches")
        ]);

        renderInventory(inventory);
        renderMatches(matches);

        document.getElementById("inventory-count").textContent =
            inventory.length;

        document.getElementById("recipe-count").textContent =
            recipes.length;

        document.getElementById("ready-count").textContent =
            matches.filter(match => match.can_prepare).length;
    } catch (error) {
        showToast(error.message);
    }
}


async function addInventory(event) {
    event.preventDefault();

    const payload = {
        name: document.getElementById("ingredient-name").value,
        quantity: Number(
            document.getElementById("ingredient-quantity").value
        ),
        unit: document.getElementById("ingredient-unit").value
    };

    try {
        await apiRequest("/api/ingredients", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        inventoryForm.reset();
        showToast("Ingredient saved.");
        await loadDashboard();
    } catch (error) {
        showToast(error.message);
    }
}


async function editInventory(item) {
    const name = prompt("Ingredient name:", item.name);

    if (name === null) {
        return;
    }

    const quantity = prompt(
        "Quantity:",
        item.quantity
    );

    if (quantity === null) {
        return;
    }

    const unit = prompt(
        `Unit (${UNIT_OPTIONS.join(", ")}):`,
        item.unit
    );

    if (unit === null) {
        return;
    }

    try {
        await apiRequest(`/api/ingredients/${item.id}`, {
            method: "PUT",
            body: JSON.stringify({
                name: name.trim(),
                quantity: Number(quantity),
                unit: unit.trim().toLowerCase()
            })
        });

        showToast("Inventory item updated.");
        await loadDashboard();
    } catch (error) {
        showToast(error.message);
    }
}


async function deleteInventory(itemId) {
    const confirmed = confirm(
        "Delete this inventory item?"
    );

    if (!confirmed) {
        return;
    }

    try {
        await apiRequest(`/api/ingredients/${itemId}`, {
            method: "DELETE"
        });

        showToast("Inventory item deleted.");
        await loadDashboard();
    } catch (error) {
        showToast(error.message);
    }
}


function renderInventory(items) {
    if (items.length === 0) {
        inventoryTable.innerHTML = `
            <tr>
                <td colspan="4" class="empty">
                    No ingredients in inventory.
                </td>
            </tr>
        `;
        return;
    }

    inventoryTable.innerHTML = items.map(item => `
        <tr>
            <td>${escapeHtml(item.name)}</td>
            <td>${formatNumber(item.quantity)}</td>
            <td>${escapeHtml(item.unit)}</td>
            <td>
                <button
                    class="secondary-button small-button"
                    data-action="edit"
                    data-id="${item.id}"
                >
                    Edit
                </button>
                <button
                    class="remove-button small-button"
                    data-action="delete"
                    data-id="${item.id}"
                >
                    Delete
                </button>
            </td>
        </tr>
    `).join("");

    inventoryTable
        .querySelectorAll("button[data-action='edit']")
        .forEach(button => {
            button.addEventListener("click", () => {
                const item = items.find(
                    value => value.id === Number(button.dataset.id)
                );

                if (item) {
                    editInventory(item);
                }
            });
        });

    inventoryTable
        .querySelectorAll("button[data-action='delete']")
        .forEach(button => {
            button.addEventListener("click", () => {
                deleteInventory(Number(button.dataset.id));
            });
        });
}


function renderMatches(matches) {
    if (matches.length === 0) {
        recipeResults.innerHTML =
            `<p class="empty">No recipes available.</p>`;
        return;
    }

    recipeResults.innerHTML = matches.map(match => {
        const statusClass = match.can_prepare
            ? "ready"
            : "blocked";

        const statusText = match.can_prepare
            ? "READY TO COOK"
            : "NOT READY";

        const ingredientRows = match.ingredients.map(item => {
            const label = describeMatch(item);

            return `
                <li class="${escapeHtml(item.status)}">
                    ${label}
                </li>
            `;
        }).join("");

        return `
            <article class="recipe-card ${statusClass}">
                <span class="status ${statusClass}">
                    ${statusText}
                </span>

                <h3>${escapeHtml(match.recipe_name)}</h3>

                <p class="recipe-meta">
                    Base recipe: ${match.recipe_servings} servings
                    · Maximum possible: ${match.maximum_servings}
                </p>

                <ul class="match-list">
                    ${ingredientRows}
                </ul>
            </article>
        `;
    }).join("");
}


function describeMatch(item) {
    const required =
        `${formatNumber(item.required_quantity)} ${item.required_unit}`;

    if (item.status === "missing") {
        return `
            <strong>${escapeHtml(item.name)}</strong>:
            missing — requires ${required}.
        `;
    }

    if (item.status === "incompatible_unit") {
        return `
            <strong>${escapeHtml(item.name)}</strong>:
            unit mismatch — ${formatNumber(item.available_quantity)}
            ${escapeHtml(item.available_unit)} available, requires ${required}.
        `;
    }

    if (item.status === "insufficient") {
        return `
            <strong>${escapeHtml(item.name)}</strong>:
            insufficient — ${formatNumber(item.available_quantity)}
            ${item.required_unit} available, requires ${required}.
        `;
    }

    return `
        <strong>${escapeHtml(item.name)}</strong>:
        available — ${formatNumber(item.available_quantity)}
        ${item.required_unit} available, requires ${required}.
    `;
}


function addRecipeIngredientRow() {
    const row = document.createElement("div");

    row.className = "recipe-ingredient-row";

    row.innerHTML = `
        <input
            type="text"
            class="recipe-ingredient-name"
            placeholder="Ingredient"
            required
            maxlength="100"
        >

        <input
            type="number"
            class="recipe-ingredient-quantity"
            placeholder="Quantity"
            min="0.0001"
            step="any"
            required
        >

        <select class="recipe-ingredient-unit">
            ${UNIT_OPTIONS.map(unit => `
                <option value="${unit}">${unit}</option>
            `).join("")}
        </select>

        <button
            type="button"
            class="remove-button small-button"
        >
            Remove
        </button>
    `;

    row
        .querySelector("button")
        .addEventListener("click", () => {
            const rows =
                recipeIngredientsContainer.children;

            if (rows.length > 1) {
                row.remove();
            }
        });

    recipeIngredientsContainer.appendChild(row);
}


async function createRecipe(event) {
    event.preventDefault();

    const rows =
        recipeIngredientsContainer.querySelectorAll(
            ".recipe-ingredient-row"
        );

    const ingredients = [];

    for (const row of rows) {
        const name =
            row.querySelector(
                ".recipe-ingredient-name"
            ).value.trim();

        const quantity =
            Number(
                row.querySelector(
                    ".recipe-ingredient-quantity"
                ).value
            );

        const unit =
            row.querySelector(
                ".recipe-ingredient-unit"
            ).value;

        if (!name || !quantity || quantity <= 0) {
            showToast(
                "Every recipe ingredient needs a valid name and quantity."
            );
            return;
        }

        ingredients.push({
            ingredient_name: name,
            quantity,
            unit
        });
    }

    const payload = {
        name:
            document.getElementById("recipe-name").value.trim(),
        servings:
            Number(
                document.getElementById("recipe-servings").value
            ),
        instructions:
            document.getElementById(
                "recipe-instructions"
            ).value,
        ingredients
    };

    try {
        await apiRequest("/api/recipes", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        recipeForm.reset();
        recipeIngredientsContainer.innerHTML = "";
        addRecipeIngredientRow();

        showToast("Recipe created.");
        await loadDashboard();
    } catch (error) {
        showToast(error.message);
    }
}


function formatNumber(value) {
    return Number(value).toLocaleString(
        undefined,
        {
            maximumFractionDigits: 2
        }
    );
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");

    window.clearTimeout(showToast.timeout);

    showToast.timeout = window.setTimeout(() => {
        toast.classList.remove("show");
    }, 3200);
}
