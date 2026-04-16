import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import init_db
from app.api.router import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.debug:
        try:
            init_db()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    yield


settings = get_settings()

app = FastAPI(
    title="BI Portal Backend API",
    description="Backend API for BI Portal Dashboard",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
# Using a more robust CORS setup for development
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add any origins from settings
extra_origins = settings.assemble_cors_origins(settings.cors_origins)
for o in extra_origins:
    if o not in origins and o != "*":
        origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in extra_origins else ["*"],
    allow_credentials=True if "*" not in extra_origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler for debugging 500 errors
# NOTE: We manually add CORS headers here because unhandled exceptions can bypass
# CORSMiddleware when propagated via Starlette's ServerErrorMiddleware.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error(f"Unhandled exception: {error_msg}")

    origin = request.headers.get("origin", "")
    allowed = [
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5173", "http://127.0.0.1:5173",
    ]
    cors_headers = {}
    if origin in allowed:
        cors_headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "msg": str(exc), "traceback": error_msg if settings.debug else None},
        headers=cors_headers,
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
