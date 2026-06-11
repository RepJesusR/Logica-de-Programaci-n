"""
Servicio UNIGIS — operaciones de Conductor.

Endpoints usados:
  - ConsultarConductor     → consulta por NroDocumento o Login
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
    login: str | None
    nombre: str | None
    apellido: str | None
    email: str | None
    telefono: str | None
    raw: dict = field(default_factory=dict, repr=False)


def _parse_conductor(data: Any) -> ConductorUnigis:
    """Convierte la respuesta zeep a un dataclass limpio."""
    # zeep devuelve objetos con atributos; usamos getattr con fallback
    def g(attr: str) -> str | None:
        val = getattr(data, attr, None)
        return str(val).strip() if val is not None else None

    return ConductorUnigis(
        nro_documento=g("NroDocumento") or "",
        login=g("Login"),
        nombre=g("Nombre"),
        apellido=g("Apellido"),
        email=g("Email"),
        telefono=g("Telefono") or g("Celular"),
        raw=dict(data) if hasattr(data, "__iter__") else {},
    )


class ConductoresService:
    def __init__(self, client: UnigisClient) -> None:
        self.client = client

    def consultar_por_documento(self, nro_documento: str) -> ConductorUnigis | None:
        """ConsultarConductor filtrado por NroDocumento."""
        try:
            result = self.client.call(
                "ConsultarConductor",
                NroDocumento=nro_documento,
            )
            if result is None:
                return None
            # La API retorna objeto único o lista según implementación MAPI
            if hasattr(result, "__iter__") and not isinstance(result, dict):
                items = list(result)
                return _parse_conductor(items[0]) if items else None
            return _parse_conductor(result)
        except Exception as exc:
            logger.warning("ConsultarConductor(%s) falló: %s", nro_documento, exc)
            return None

    def listar_todos(self) -> list[ConductorUnigis]:
        """
        ConsultarConductores — obtiene la lista completa de conductores.

        UNIGIS MAPI puede devolver esto bajo varios nombres según versión:
        ConsultarConductores, ObtenerConductores, GetConductores.
        Probamos el más común primero.
        """
        for op in ("ConsultarConductores", "ObtenerConductores", "GetConductores"):
            try:
                result = self.client.call(op)
                if result is None:
                    continue
                items = result if hasattr(result, "__iter__") else [result]
                conductores = []
                for item in items:
                    try:
                        conductores.append(_parse_conductor(item))
                    except Exception as parse_err:
                        logger.debug("Parse conductor falló: %s", parse_err)
                logger.info("UNIGIS devolvió %d conductores via %s", len(conductores), op)
                return conductores
            except Exception as exc:
                logger.debug("%s no disponible: %s", op, exc)
        logger.error("No se pudo obtener lista de conductores de UNIGIS")
        return []
