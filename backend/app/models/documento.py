import uuid
import enum
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, ForeignKey, Integer, Enum, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EstadoDocumento(str, enum.Enum):
    VIGENTE = "VIGENTE"
    POR_VENCER = "POR_VENCER"
    VENCIDO = "VENCIDO"
    SIN_DOCUMENTO = "SIN_DOCUMENTO"


class Documento(Base):
    __tablename__ = "documentos"
    __table_args__ = (
        # Un conductor tiene un registro por tipo de documento
        UniqueConstraint("conductor_id", "tipo_documento_id_unigis", name="uq_conductor_tipo_doc"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, primary_key=True, index=True
    )
    conductor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conductores.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Identificadores de UNIGIS (no hacemos FK a UNIGIS, solo guardamos las refs)
    documento_id_unigis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tipo_documento_id_unigis: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo_documento_nombre: Mapped[str] = mapped_column(String(200), nullable=False)

    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    dias_preaviso: Mapped[int] = mapped_column(Integer, default=15)

    estado: Mapped[EstadoDocumento] = mapped_column(
        Enum(EstadoDocumento), nullable=False, default=EstadoDocumento.SIN_DOCUMENTO
    )
    dias_para_vencer: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamp del último sync desde UNIGIS
    ultimo_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    conductor: Mapped["Conductor"] = relationship(back_populates="documentos")
    notificaciones: Mapped[list["Notificacion"]] = relationship(back_populates="documento")
