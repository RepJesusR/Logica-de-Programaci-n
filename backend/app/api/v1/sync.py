"""
Endpoints de sync manual — para forzar sincronización sin esperar el scheduler.
El sync corre en background para no bloquear la respuesta HTTP.
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.tenant import Tenant
from app.services.compliance.monitor import ComplianceMonitor
from app.services.notifications.dispatcher import NotificationDispatcher

router = APIRouter()
logger = logging.getLogger(__name__)


async def _run_sync_background(tenant_id: str) -> None:
    """Job de sync que abre su propia sesión DB (background task)."""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = result.scalar_one_or_none()
            if not tenant:
                logger.error("Sync background: tenant %s no encontrado", tenant_id)
                return
            monitor = ComplianceMonitor(db)
            stats = await monitor.sync_tenant(tenant)
            await db.commit()
            logger.info("Sync background completado: %s", stats)
        except Exception as exc:
            await db.rollback()
            logger.error("Sync background falló para tenant %s: %s", tenant_id, exc, exc_info=True)


async def _run_notif_background(tenant_id: str) -> None:
    """Job de notificaciones que abre su propia sesión DB (background task)."""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = result.scalar_one_or_none()
            if not tenant:
                return
            dispatcher = NotificationDispatcher(db)
            stats = await dispatcher.procesar_tenant(tenant)
            await db.commit()
            logger.info("Notificaciones background completadas: %s", stats)
        except Exception as exc:
            await db.rollback()
            logger.error("Notif background falló para tenant %s: %s", tenant_id, exc, exc_info=True)


@router.post("/{tenant_slug}/documentos", status_code=202)
async def sync_documentos(
    tenant_slug: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Fuerza sync de documentos desde UNIGIS para el tenant.
    Responde 202 inmediatamente; el sync corre en background.
    """
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    background_tasks.add_task(_run_sync_background, str(tenant.id))
    return {"mensaje": "Sync iniciado en background", "tenant": tenant_slug}


@router.post("/{tenant_slug}/notificaciones", status_code=202)
async def enviar_notificaciones(
    tenant_slug: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Dispara envío de notificaciones para documentos con alertas pendientes.
    Responde 202 inmediatamente; el envío corre en background.
    """
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    background_tasks.add_task(_run_notif_background, str(tenant.id))
    return {"mensaje": "Notificaciones iniciadas en background", "tenant": tenant_slug}
