from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db, seed_demo_data
from .routers import inventory, matching, recipes


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_demo_data()
    yield


app = FastAPI(
    title="CookBase API",
    version="1.0.0",
    description=(
        "A simple cooking assistant for ingredient inventory, "
        "recipes, and availability matching."
    ),
    lifespan=lifespan,
)

app.include_router(inventory.router)
app.include_router(recipes.router)
app.include_router(matching.router)

STATIC_DIR = "app/static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "cookbase",
    }


@app.get("/")
def home():
    return FileResponse(f"{STATIC_DIR}/index.html")
