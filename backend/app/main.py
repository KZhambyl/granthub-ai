from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as grants_router
from app.init_db import init_db

app = FastAPI(title="GrantHub.AI")

init_db()

app.include_router(grants_router, prefix="/api/v1", tags=["Grants"])
