import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import init_db
from app.api.router import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.services.scheduler import scheduler, init_scheduler
from app.services.deno_service import deno_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.debug:
        try:
            init_db()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    init_scheduler()
    await deno_service.cache_runner_deps()

    # Limpiar ejecuciones que quedaron en "running" por un reinicio inesperado
    try:
        from datetime import datetime
        from app.core.database import SessionLocal
        from app.models import models as _models
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            stuck = db.query(_models.ExecutionHistory).filter(_models.ExecutionHistory.status == "running").all()
            for ex in stuck:
                ex.status = "aborted"
                ex.end_time = now
                if ex.start_time:
                    ex.duration = int((now - ex.start_time).total_seconds())
            if stuck:
                db.commit()
                logger.warning(f"Startup cleanup: {len(stuck)} ejecuciones 'running' marcadas como 'aborted'")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Startup cleanup failed: {e}")

    yield
    scheduler.shutdown()


settings = get_settings()

app = FastAPI(
    title="BI Portal Backend API",
    description="Backend API for BI Portal Dashboard",
    version="0.1.0",
    lifespan=lifespan
)

# Global error handler for debugging 500 errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error(f"Unhandled exception: {error_msg}")

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "msg": str(exc), "traceback": error_msg if settings.debug else None},
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
