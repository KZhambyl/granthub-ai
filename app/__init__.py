from fastapi import FastAPI
from app.api.routes.routes import router as base_router
from contextlib import asynccontextmanager
from app.db.main import init_db
from app.auth.routes import auth_router
from app.middlewares.middleware import register_middleware
from demo_front.router import router as demo_front_router


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
    docs_url=f"/api/{version}/docs",
    redoc_url=f"/api/{version}/redoc"
)

register_middleware(app)

app.include_router(base_router, prefix=f"/api/{version}")
app.include_router(auth_router, prefix=f"/api/{version}/auth", tags=['Auth'])
app.include_router(demo_front_router)
