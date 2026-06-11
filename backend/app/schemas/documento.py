import uuid
from datetime import date, datetime
from pydantic import BaseModel
from app.models.documento import EstadoDocumento


class DocumentoRead(BaseModel):
    id: uuid.UUID
    conductor_id: uuid.UUID
    tipo_documento_nombre: str
    fecha_vencimiento: date | None
    dias_preaviso: int
    estado: EstadoDocumento
    dias_para_vencer: int | None
    ultimo_sync: datetime | None

    model_config = {"from_attributes": True}


class ResumenFlota(BaseModel):
    total: int
    vigente: int
    por_vencer: int
    vencido: int
    sin_documento: int
