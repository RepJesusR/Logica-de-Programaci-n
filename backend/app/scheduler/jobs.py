"""
Jobs programados con APScheduler.

Jobs:
  sync_all_tenants    → cada N minutos, sincroniza docs desde UNIGIS
  notify_all_tenants  → diariamente a las 08:00 UTC, envía notificaciones
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.services.compliance.monitor import ComplianceMonitor
from app.services.notifications.dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _sync_all_tenants() -> None:
    logger.info("Job: sync_all_tenants iniciado")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tenant).where(Tenant.activo == True))
        tenants = result.scalars().all()
        monitor = ComplianceMonitor(db)
        for tenant in tenants:
            try:
                stats = await monitor.sync_tenant(tenant)
                logger.info("Sync OK — %s", stats)
            except Exception as exc:
                logger.error("Sync falló para %s: %s", tenant.slug, exc)
        await db.commit()


async def _notify_all_tenants() -> None:
    logger.info("Job: notify_all_tenants iniciado")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tenant).where(Tenant.activo == True))
        tenants = result.scalars().all()
        dispatcher = NotificationDispatcher(db)
        for tenant in tenants:
            try:
                stats = await dispatcher.procesar_tenant(tenant)
                logger.info("Notificaciones OK — %s | %s", tenant.slug, stats)
            except Exception as exc:
                logger.error("Notificaciones fallaron para %s: %s", tenant.slug, exc)
        await db.commit()


def create_scheduler() -> AsyncIOScheduler:
    global _scheduler
    settings = get_settings()

    _scheduler = AsyncIOScheduler(timezone="UTC")

    _scheduler.add_job(
        _sync_all_tenants,
        trigger=IntervalTrigger(minutes=settings.SYNC_INTERVAL_MINUTES),
        id="sync_all_tenants",
        name="Sync documentos UNIGIS",
        replace_existing=True,
        misfire_grace_time=300,
    )

    _scheduler.add_job(
        _notify_all_tenants,
        trigger=CronTrigger(
            hour=settings.NOTIFY_JOB_HOUR,
            minute=settings.NOTIFY_JOB_MINUTE,
        ),
        id="notify_all_tenants",
        name="Envío de notificaciones diarias",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    return _scheduler


def get_scheduler() -> AsyncIOScheduler:
    if _scheduler is None:
        return create_scheduler()
    return _scheduler
