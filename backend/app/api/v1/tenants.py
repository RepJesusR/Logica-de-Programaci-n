from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantRead

router = APIRouter()


@router.get("/", response_model=list[TenantRead])
async def listar_tenants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).order_by(Tenant.nombre))
    return result.scalars().all()


@router.post("/", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def crear_tenant(payload: TenantCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Tenant).where(Tenant.slug == payload.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slug ya existe")

    tenant = Tenant(**payload.model_dump())
    db.add(tenant)
    await db.flush()
    return tenant


@router.get("/{tenant_slug}", response_model=TenantRead)
async def obtener_tenant(tenant_slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Tenant).where(Tenant.slug == tenant_slug)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant
