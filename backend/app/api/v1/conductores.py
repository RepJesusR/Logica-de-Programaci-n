from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conductor import Conductor
from app.models.tenant import Tenant
from app.schemas.conductor import ConductorRead

router = APIRouter()


async def _get_tenant(tenant_slug: str, db: AsyncSession) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant


@router.get("/{tenant_slug}", response_model=list[ConductorRead])
async def listar_conductores(
    tenant_slug: str,
    search: str | None = Query(None, description="Busca por nombre o nro_documento"),
    db: AsyncSession = Depends(get_db),
):
    tenant = await _get_tenant(tenant_slug, db)
    stmt = select(Conductor).where(Conductor.tenant_id == tenant.id)
    if search:
        like = f"%{search}%"
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(
                Conductor.nro_documento.ilike(like),
                Conductor.nombre.ilike(like),
                Conductor.apellido.ilike(like),
            )
        )
    result = await db.execute(stmt.order_by(Conductor.apellido, Conductor.nombre))
    return result.scalars().all()


@router.get("/{tenant_slug}/{conductor_id}", response_model=ConductorRead)
async def obtener_conductor(
    tenant_slug: str,
    conductor_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    tenant = await _get_tenant(tenant_slug, db)
    result = await db.execute(
        select(Conductor).where(
            Conductor.id == conductor_id,
            Conductor.tenant_id == tenant.id,
        )
    )
    conductor = result.scalar_one_or_none()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    return conductor
