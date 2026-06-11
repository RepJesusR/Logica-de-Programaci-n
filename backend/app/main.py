import logging

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1.router import api_router
from app.scheduler.jobs import create_scheduler

logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

settings = get_settings()

app = FastAPI(
    title="Zuvra Compliance API",
    description="Monitor de documentos para flotas logísticas — integrado con UNIGIS MAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.on_event("startup")
async def startup():
    logger.info("Zuvra API arrancando", env=settings.APP_ENV)
    scheduler = create_scheduler()
    scheduler.start()
    logger.info(
        "Scheduler iniciado",
        jobs=[j.id for j in scheduler.get_jobs()],
    )


@app.on_event("shutdown")
async def shutdown():
    from app.scheduler.jobs import get_scheduler
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
    logger.info("Zuvra API detenida")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "zuvra-compliance"}
