from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import init_db
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.debug:
        init_db()
    yield


settings = get_settings()

app = FastAPI(
    title="BI Portal Backend API",
    description="Backend API for BI Portal Dashboard",
    version="0.1.0",
    lifespan=lifespan
)

# Use explicit origins if provided, otherwise default to common dev/qa origins
origins = settings.assemble_cors_origins(settings.cors_origins)
if "*" in origins:
    # If wildcard is used, we can't allow credentials, but we can't do that if frontend needs auth
    # For dev/testing we can use a permissive list or regex
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root():
    return {"message": "BI Portal API is running", "health_check": "/health"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)