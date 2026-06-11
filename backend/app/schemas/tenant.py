import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    nombre: str = Field(..., max_length=120)
    slug: str = Field(..., max_length=60, pattern=r"^[a-z0-9\-]+$")
    unigis_wsdl_url: str
    unigis_api_key: str
    unigis_login: str
    unigis_password: str
    dias_preaviso_default: int = 15
    notificar_whatsapp: bool = True
    notificar_email: bool = True
    admin_email: str | None = None
    admin_whatsapp: str | None = None


class TenantRead(BaseModel):
    id: uuid.UUID
    nombre: str
    slug: str
    dias_preaviso_default: int
    notificar_whatsapp: bool
    notificar_email: bool
    admin_email: str | None
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}
