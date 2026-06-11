"""
Endpoints de sync manual — útiles durante el piloto para forzar una sincronización
sin esperar el scheduler.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tenant import Tenant
from app.services.compliance.monitor import ComplianceMonitor
from app.services.notifications.dispatcher import NotificationDispatcher

router = APIRouter()


@router.post("/{tenant_slug}/documentos")
async def sync_documentos(
    tenant_slug: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Fuerza sync de documentos desde UNIGIS para el tenant."""
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    monitor = ComplianceMonitor(db)
    stats = await monitor.sync_tenant(tenant)
    return {"mensaje": "Sync completado", "stats": stats}


@router.post("/{tenant_slug}/notificaciones")
async def enviar_notificaciones(
    tenant_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Dispara envío de notificaciones para documentos con alertas pendientes."""
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    dispatcher = NotificationDispatcher(db)
    stats = await dispatcher.procesar_tenant(tenant)
    return {"mensaje": "Notificaciones procesadas", "stats": stats}
