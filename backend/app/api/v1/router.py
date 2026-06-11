from fastapi import APIRouter
from app.api.v1 import conductores, documentos, dashboard, tenants, sync

api_router = APIRouter()
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(conductores.router, prefix="/conductores", tags=["conductores"])
api_router.include_router(documentos.router, prefix="/documentos", tags=["documentos"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
