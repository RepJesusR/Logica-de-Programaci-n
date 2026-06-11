import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Conductor(Base):
    __tablename__ = "conductores"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nro_documento", name="uq_tenant_nro_documento"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, primary_key=True, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Campos sincronizados desde UNIGIS
    nro_documento: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    login: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nombre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    apellido: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Último sync exitoso con UNIGIS
    ultimo_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="conductores")
    documentos: Mapped[list["Documento"]] = relationship(back_populates="conductor")

    @property
    def nombre_completo(self) -> str:
        partes = [self.nombre, self.apellido]
        return " ".join(p for p in partes if p) or self.nro_documento
