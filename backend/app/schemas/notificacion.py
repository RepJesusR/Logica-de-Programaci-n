import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.notificacion import CanalNotificacion


class NotificacionRead(BaseModel):
    id: uuid.UUID
    documento_id: uuid.UUID
    canal: CanalNotificacion
    destinatario: str
    asunto: str | None
    enviado_ok: bool
    fecha_envio: datetime

    model_config = {"from_attributes": True}
