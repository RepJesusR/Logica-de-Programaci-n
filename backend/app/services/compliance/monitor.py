"""
ComplianceMonitor — núcleo de Zuvra Compliance.

Flujo por tenant:
  1. Obtener lista de conductores desde UNIGIS
  2. Upsert conductores en DB local
  3. Para cada conductor, obtener documentos desde UNIGIS
  4. Calcular estado (VIGENTE / POR_VENCER / VENCIDO / SIN_DOCUMENTO)
  5. Upsert documentos en DB local
"""
import logging
from datetime import date, datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conductor import Conductor
from app.models.documento import Documento, EstadoDocumento
from app.models.tenant import Tenant
from app.services.unigis.client import UnigisClient
from app.services.unigis.conductores import ConductoresService, ConductorUnigis
from app.services.unigis.documentos import DocumentosService, DocumentoUnigis

logger = logging.getLogger(__name__)


def _calcular_estado(
    fecha_vencimiento: date | None,
    dias_preaviso: int,
) -> tuple[EstadoDocumento, int | None]:
    """
    Retorna (estado, dias_para_vencer).
    dias_para_vencer es negativo si ya venció.
    """
    if fecha_vencimiento is None:
        return EstadoDocumento.SIN_DOCUMENTO, None

    hoy = date.today()
    delta = (fecha_vencimiento - hoy).days

    if delta < 0:
        return EstadoDocumento.VENCIDO, delta
    elif delta <= dias_preaviso:
        return EstadoDocumento.POR_VENCER, delta
    else:
        return EstadoDocumento.VIGENTE, delta


class ComplianceMonitor:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def sync_tenant(self, tenant: Tenant) -> dict:
        """Ejecuta el ciclo completo de sync para un tenant. Retorna estadísticas."""
        stats = {
            "tenant_id": str(tenant.id),
            "tenant_slug": tenant.slug,
            "conductores_procesados": 0,
            "documentos_upserted": 0,
            "por_vencer": 0,
            "vencidos": 0,
            "errores": 0,
        }

        client = UnigisClient.from_tenant(tenant)
        conductores_svc = ConductoresService(client)
        documentos_svc = DocumentosService(client)

        conductores_unigis = await conductores_svc.listar_todos()
        if not conductores_unigis:
            logger.warning("Tenant %s: sin conductores en UNIGIS", tenant.slug)
            return stats

        now = datetime.now(tz=timezone.utc)

        for c_uni in conductores_unigis:
            if not c_uni.nro_documento:
                continue
            try:
                conductor = await self._upsert_conductor(tenant, c_uni, now)
                docs_unigis = await documentos_svc.obtener_por_conductor(
                    c_uni.nro_documento,
                    id_conductor=c_uni.id_conductor,
                )
                doc_stats = await self._upsert_documentos(
                    conductor, docs_unigis, tenant.dias_preaviso_default, now
                )
                stats["conductores_procesados"] += 1
                stats["documentos_upserted"] += doc_stats["upserted"]
                stats["por_vencer"] += doc_stats["por_vencer"]
                stats["vencidos"] += doc_stats["vencidos"]
            except Exception as exc:
                logger.error(
                    "Tenant %s / conductor %s: error en sync: %s",
                    tenant.slug, c_uni.nro_documento, exc,
                    exc_info=True,
                )
                stats["errores"] += 1

        logger.info("Sync completado: %s", stats)
        return stats

    async def _upsert_conductor(
        self,
        tenant: Tenant,
        c_uni: ConductorUnigis,
        now: datetime,
    ) -> Conductor:
        stmt = select(Conductor).where(
            Conductor.tenant_id == tenant.id,
            Conductor.nro_documento == c_uni.nro_documento,
        )
        result = await self.db.execute(stmt)
        conductor = result.scalar_one_or_none()

        if conductor is None:
            conductor = Conductor(
                tenant_id=tenant.id,
                nro_documento=c_uni.nro_documento,
            )
            self.db.add(conductor)

        conductor.id_conductor_unigis = c_uni.id_conductor
        conductor.login = c_uni.login
        conductor.nombre = c_uni.nombre
        conductor.apellido = c_uni.apellido
        conductor.email = c_uni.email
        conductor.telefono = c_uni.telefono
        conductor.ultimo_sync = now
        await self.db.flush()
        return conductor

    async def _upsert_documentos(
        self,
        conductor: Conductor,
        docs_unigis: list[DocumentoUnigis],
        dias_preaviso_default: int,
        now: datetime,
    ) -> dict:
        stats = {"upserted": 0, "por_vencer": 0, "vencidos": 0}

        # Deduplicar por tipo_documento_id para evitar viola única constraint
        seen_tipos: set[int] = set()

        for doc_uni in docs_unigis:
            if doc_uni.tipo_documento_id in seen_tipos:
                logger.warning(
                    "Conductor %s: tipo_documento_id %s duplicado en respuesta UNIGIS, ignorando",
                    conductor.nro_documento, doc_uni.tipo_documento_id,
                )
                continue
            seen_tipos.add(doc_uni.tipo_documento_id)

            dias_preaviso = doc_uni.dias_preaviso or dias_preaviso_default
            estado, dias_para_vencer = _calcular_estado(
                doc_uni.fecha_vencimiento, dias_preaviso
            )

            stmt = select(Documento).where(
                Documento.conductor_id == conductor.id,
                Documento.tipo_documento_id_unigis == doc_uni.tipo_documento_id,
            )
            result = await self.db.execute(stmt)
            doc = result.scalar_one_or_none()

            if doc is None:
                doc = Documento(
                    conductor_id=conductor.id,
                    tipo_documento_id_unigis=doc_uni.tipo_documento_id,
                )
                self.db.add(doc)

            doc.documento_id_unigis = doc_uni.documento_id
            doc.tipo_documento_nombre = doc_uni.tipo_documento_nombre
            doc.fecha_vencimiento = doc_uni.fecha_vencimiento
            doc.dias_preaviso = dias_preaviso
            doc.estado = estado
            doc.dias_para_vencer = dias_para_vencer
            doc.ultimo_sync = now

            await self.db.flush()
            stats["upserted"] += 1

            if estado == EstadoDocumento.POR_VENCER:
                stats["por_vencer"] += 1
            elif estado == EstadoDocumento.VENCIDO:
                stats["vencidos"] += 1

        return stats

    async def get_resumen_flota(self, tenant_id) -> dict:
        """Resumen de estado documental de toda la flota para el dashboard."""
        totals_q = await self.db.execute(
            select(Documento.estado, func.count())
            .join(Conductor)
            .where(Conductor.tenant_id == tenant_id)
            .group_by(Documento.estado)
        )

        conteos = {row[0]: row[1] for row in totals_q.fetchall()}
        total = sum(conteos.values())
        return {
            "total": total,
            "vigente": conteos.get(EstadoDocumento.VIGENTE, 0),
            "por_vencer": conteos.get(EstadoDocumento.POR_VENCER, 0),
            "vencido": conteos.get(EstadoDocumento.VENCIDO, 0),
            "sin_documento": conteos.get(EstadoDocumento.SIN_DOCUMENTO, 0),
        }
