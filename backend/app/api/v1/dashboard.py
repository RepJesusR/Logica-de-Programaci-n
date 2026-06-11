from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tenant import Tenant
from app.schemas.documento import ResumenFlota
from app.services.compliance.monitor import ComplianceMonitor

router = APIRouter()


@router.get("/{tenant_slug}/resumen", response_model=ResumenFlota)
async def resumen_flota(
    tenant_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Resumen de estado documental de toda la flota — para el panel principal."""
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    monitor = ComplianceMonitor(db)
    resumen = await monitor.get_resumen_flota(tenant.id)
    return ResumenFlota(**resumen)


@router.get("/{tenant_slug}/criticos")
async def conductores_criticos(
    tenant_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Conductores con al menos un documento VENCIDO o POR_VENCER."""
    from sqlalchemy import distinct
    from app.models.conductor import Conductor
    from app.models.documento import Documento, EstadoDocumento
    from app.schemas.conductor import ConductorRead

    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    stmt = (
        select(Conductor)
        .join(Documento)
        .where(
            Conductor.tenant_id == tenant.id,
            Documento.estado.in_([EstadoDocumento.VENCIDO, EstadoDocumento.POR_VENCER]),
        )
        .distinct()
        .order_by(Conductor.apellido, Conductor.nombre)
    )
    result = await db.execute(stmt)
    conductores = result.scalars().all()
    return [ConductorRead.model_validate(c) for c in conductores]
