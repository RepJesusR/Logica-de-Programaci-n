"""
Servicio UNIGIS — operaciones de Conductor.

Endpoints usados:
  - ConsultarConductor     → consulta por NroDocumento
  - ConsultarConductores   → lista todos los conductores activos
"""
import logging
from dataclasses import dataclass, field
from typing import Any

from app.services.unigis.client import UnigisClient

logger = logging.getLogger(__name__)


@dataclass
class ConductorUnigis:
    nro_documento: str
    id_conductor: int | None      # IdConductor UNIGIS — usado como fallback en ObtenerDocumentosEntidad
    login: str | None
    nombre: str | None
    apellido: str | None
    email: str | None
    telefono: str | None
    raw: dict = field(default_factory=dict, repr=False)


def _parse_conductor(data: Any) -> ConductorUnigis:
    """Convierte la respuesta zeep a un dataclass limpio."""
    def g(attr: str) -> str | None:
        val = getattr(data, attr, None)
        return str(val).strip() if val is not None else None

    _id_raw = getattr(data, "IdConductor", None)
    return ConductorUnigis(
        nro_documento=g("NroDocumento") or "",
        id_conductor=int(_id_raw) if _id_raw is not None else None,
        login=g("Login"),
        nombre=g("Nombre"),
        apellido=g("Apellido"),
        email=g("EMail") or g("Email"),
        telefono=g("Telefono") or g("Celular"),
        raw={},
    )


class ConductoresService:
    def __init__(self, client: UnigisClient) -> None:
        self.client = client

    async def consultar_por_documento(self, nro_documento: str) -> ConductorUnigis | None:
        """ConsultarConductor filtrado por NroDocumento."""
        try:
            result = await self.client.call(
                "ConsultarConductor",
                NroDocumento=nro_documento,
            )
            if result is None:
                return None
            if hasattr(result, "__iter__") and not isinstance(result, (str, dict)):
                items = list(result)
                return _parse_conductor(items[0]) if items else None
            return _parse_conductor(result)
        except Exception as exc:
            logger.warning("ConsultarConductor(%s) falló: %s", nro_documento, exc)
            return None

    async def listar_todos(self) -> list[ConductorUnigis]:
        """
        Obtiene la lista completa de conductores.

        UNIGIS MAPI puede exponer este endpoint bajo distintos nombres según versión.
        Se prueba en orden hasta encontrar el que funciona.
        """
        for op in ("ConsultarConductores", "ObtenerConductores", "GetConductores"):
            try:
                result = await self.client.call(op)
                if result is None:
                    continue
                items = result if hasattr(result, "__iter__") and not isinstance(result, (str, dict)) else [result]
                conductores = []
                for item in items:
                    try:
                        c = _parse_conductor(item)
                        if c.nro_documento:
                            conductores.append(c)
                    except Exception as parse_err:
                        logger.debug("Parse conductor falló: %s", parse_err)
                logger.info("UNIGIS: %d conductores obtenidos via %s", len(conductores), op)
                return conductores
            except Exception as exc:
                logger.debug("%s no disponible: %s", op, exc)
        logger.error("No se pudo obtener lista de conductores de UNIGIS")
        return []
