import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, primary_key=True, index=True
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)

    unigis_wsdl_url: Mapped[str] = mapped_column(String(500), nullable=False)
    unigis_api_key: Mapped[str] = mapped_column(String(200), nullable=False)
    unigis_login: Mapped[str] = mapped_column(String(100), nullable=False)
    unigis_password: Mapped[str] = mapped_column(String(200), nullable=False)

    # Días de preaviso por defecto si TipoDocumento no lo especifica
    dias_preaviso_default: Mapped[int] = mapped_column(default=15)

    notificar_whatsapp: Mapped[bool] = mapped_column(Boolean, default=True)
    notificar_email: Mapped[bool] = mapped_column(Boolean, default=True)

    # Email/WhatsApp del administrador de flota
    admin_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    admin_whatsapp: Mapped[str | None] = mapped_column(String(30), nullable=True)

    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    conductores: Mapped[list["Conductor"]] = relationship(back_populates="tenant")
