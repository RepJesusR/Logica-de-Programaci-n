import uuid
from datetime import datetime
from pydantic import BaseModel


class ConductorRead(BaseModel):
    id: uuid.UUID
    nro_documento: str
    nombre: str | None
    apellido: str | None
    email: str | None
    telefono: str | None
    ultimo_sync: datetime | None

    model_config = {"from_attributes": True}
