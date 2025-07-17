from fastapi import FastAPI
from .api.routes.routes import router as base_router
from contextlib import asynccontextmanager
from .db.main import init_db
from .auth.routes import auth_router

@asynccontextmanager
async def life_span(app: FastAPI):
    print(f"server is starting ... ")
    await init_db()
    yield
    print(f"server has been stopped")

version = "v1"

app = FastAPI(
    title = "GrantHub.AI",
    description = "A REST API for a opportunities review web service",
    version = version,
    lifespan=life_span
)

app.include_router(base_router, prefix=f"/api/{version}")
app.include_router(auth_router, prefix="/api/{version}/auth", tags=['auth'])
