import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CanalNotificacion(str, enum.Enum):
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"


class Notificacion(Base):
    """Log inmutable de notificaciones enviadas — evita duplicados y audita envíos."""
    __tablename__ = "notificaciones"

    id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, primary_key=True, index=True
    )
    documento_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    canal: Mapped[CanalNotificacion] = mapped_column(Enum(CanalNotificacion), nullable=False)
    destinatario: Mapped[str] = mapped_column(String(200), nullable=False)
    asunto: Mapped[str | None] = mapped_column(String(300), nullable=True)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)

    # SID de Twilio o message_id de SendGrid para rastreo externo
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    enviado_ok: Mapped[bool] = mapped_column(default=False)
    error_detalle: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Para deduplicar: no enviamos la misma alerta el mismo día por el mismo canal
    fecha_envio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    documento: Mapped["Documento"] = relationship(back_populates="notificaciones")
