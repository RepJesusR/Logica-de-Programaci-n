from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conductor import Conductor
from app.models.documento import Documento, EstadoDocumento
from app.models.tenant import Tenant
from app.schemas.documento import DocumentoRead

router = APIRouter()


@router.get("/{tenant_slug}", response_model=list[DocumentoRead])
async def listar_documentos(
    tenant_slug: str,
    estado: EstadoDocumento | None = Query(None),
    conductor_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Lista documentos del tenant, opcionalmente filtrados por estado o conductor."""
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    stmt = (
        select(Documento)
        .join(Conductor)
        .where(Conductor.tenant_id == tenant.id)
    )
    if estado:
        stmt = stmt.where(Documento.estado == estado)
    if conductor_id:
        stmt = stmt.where(Documento.conductor_id == conductor_id)

    stmt = stmt.order_by(Documento.fecha_vencimiento.asc().nullsfirst())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{tenant_slug}/conductor/{conductor_id}", response_model=list[DocumentoRead])
async def documentos_de_conductor(
    tenant_slug: str,
    conductor_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Documentos de un conductor específico con su estado."""
    result = await db.execute(
        select(Conductor).where(Conductor.id == conductor_id)
    )
    conductor = result.scalar_one_or_none()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")

    result = await db.execute(
        select(Documento)
        .where(Documento.conductor_id == conductor_id)
        .order_by(Documento.tipo_documento_nombre)
    )
    return result.scalars().all()
