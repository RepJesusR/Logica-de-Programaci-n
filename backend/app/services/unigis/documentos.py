"""
Servicio UNIGIS — operaciones de Documentos de Entidad.

Endpoints usados:
  - ObtenerDocumentosEntidad          → Entidad="Conductor", Referencia=NroDocumento
  - ConsultarCantidadDocumentosPorEstado → resumen estadístico
  - CrearDocumentos                   → upload de archivo en base64
"""
import base64
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.services.unigis.client import UnigisClient

logger = logging.getLogger(__name__)

ENTIDAD_CONDUCTOR = "Conductor"


@dataclass
class DocumentoUnigis:
    documento_id: int | None
    tipo_documento_id: int
    tipo_documento_nombre: str
    fecha_vencimiento: date | None
    dias_preaviso: int
    notificar_mobile: bool
    raw: dict = field(default_factory=dict, repr=False)


def _parse_fecha(valor: Any) -> date | None:
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor
    try:
        from datetime import datetime
        s = str(valor).split("T")[0]
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_documento(data: Any) -> DocumentoUnigis:
    def g(attr: str) -> Any:
        return getattr(data, attr, None)

    return DocumentoUnigis(
        documento_id=int(g("IdDocumento") or 0) or None,
        tipo_documento_id=int(g("IdTipoDocumento") or 0),
        tipo_documento_nombre=str(g("TipoDocumento") or g("Descripcion") or ""),
        fecha_vencimiento=_parse_fecha(g("FechaVencimiento")),
        dias_preaviso=int(g("DiasPreavisoVencimiento") or 15),
        notificar_mobile=bool(g("NotificarMobile")),
        raw={},
    )


class DocumentosService:
    def __init__(self, client: UnigisClient) -> None:
        self.client = client

    async def obtener_por_conductor(self, nro_documento: str) -> list[DocumentoUnigis]:
        """ObtenerDocumentosEntidad con Entidad=Conductor y Referencia=NroDocumento."""
        try:
            result = await self.client.call(
                "ObtenerDocumentosEntidad",
                Entidad=ENTIDAD_CONDUCTOR,
                Referencia=nro_documento,
            )
            if result is None:
                return []
            items = result if hasattr(result, "__iter__") and not isinstance(result, (str, dict)) else [result]
            documentos = []
            for item in items:
                try:
                    documentos.append(_parse_documento(item))
                except Exception as err:
                    logger.debug("Parse documento falló: %s", err)
            return documentos
        except Exception as exc:
            logger.warning("ObtenerDocumentosEntidad(%s) falló: %s", nro_documento, exc)
            return []

    async def cantidad_por_estado(self) -> dict[str, int]:
        """ConsultarCantidadDocumentosPorEstado — resumen para el dashboard."""
        try:
            result = await self.client.call("ConsultarCantidadDocumentosPorEstado")
            if result is None:
                return {}
            return {
                "VIGENTE": int(getattr(result, "Vigentes", 0) or 0),
                "POR_VENCER": int(getattr(result, "PorVencer", 0) or 0),
                "VENCIDO": int(getattr(result, "Vencidos", 0) or 0),
            }
        except Exception as exc:
            logger.warning("ConsultarCantidadDocumentosPorEstado falló: %s", exc)
            return {}

    async def crear_documento(
        self,
        nro_documento_conductor: str,
        tipo_documento_id: int,
        fecha_vencimiento: date,
        archivo_bytes: bytes,
        nombre_archivo: str,
    ) -> bool:
        """CrearDocumentos — sube un archivo en base64 para un conductor."""
        try:
            archivo_b64 = base64.b64encode(archivo_bytes).decode()
            result = await self.client.call(
                "CrearDocumentos",
                Entidad=ENTIDAD_CONDUCTOR,
                Referencia=nro_documento_conductor,
                IdTipoDocumento=tipo_documento_id,
                FechaVencimiento=fecha_vencimiento.isoformat(),
                NombreArchivo=nombre_archivo,
                Archivo=archivo_b64,
            )
            return result is not None
        except Exception as exc:
            logger.error("CrearDocumentos falló para %s: %s", nro_documento_conductor, exc)
            return False
