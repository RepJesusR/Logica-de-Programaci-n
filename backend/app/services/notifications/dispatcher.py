"""
NotificationDispatcher — orquesta envíos con deduplicación diaria.

Regla: no enviamos la misma alerta (mismo documento, mismo canal, mismo día).
Notifica al conductor (si tiene teléfono/email) y al admin del tenant (si está configurado).
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conductor import Conductor
from app.models.documento import Documento, EstadoDocumento
from app.models.notificacion import Notificacion, CanalNotificacion
from app.models.tenant import Tenant
from app.services.notifications.whatsapp import WhatsAppService, build_mensaje_vencimiento
from app.services.notifications.email import EmailService, build_html_vencimiento

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        # Inicialización lazy: no crashear si las credenciales no están configuradas
        self._wa: WhatsAppService | None = None
        self._email: EmailService | None = None

    def _get_wa(self) -> WhatsAppService | None:
        if self._wa is None:
            try:
                self._wa = WhatsAppService()
            except Exception as exc:
                logger.warning("WhatsAppService no disponible: %s", exc)
        return self._wa

    def _get_email(self) -> EmailService | None:
        if self._email is None:
            try:
                self._email = EmailService()
            except Exception as exc:
                logger.warning("EmailService no disponible: %s", exc)
        return self._email

    async def procesar_tenant(self, tenant: Tenant) -> dict:
        """Envía notificaciones para todos los documentos POR_VENCER y VENCIDOS del tenant."""
        stats = {"enviados": 0, "omitidos": 0, "errores": 0}

        stmt = (
            select(Documento, Conductor)
            .join(Conductor)
            .where(
                Conductor.tenant_id == tenant.id,
                Documento.estado.in_([EstadoDocumento.POR_VENCER, EstadoDocumento.VENCIDO]),
            )
        )
        result = await self.db.execute(stmt)
        rows = result.fetchall()

        for doc, conductor in rows:
            try:
                sent = await self._enviar_si_necesario(doc, conductor, tenant)
                stats["enviados"] += sent
                if sent == 0:
                    stats["omitidos"] += 1
            except Exception as exc:
                logger.error("Error notificando doc %s: %s", doc.id, exc)
                stats["errores"] += 1

        return stats

    async def _ya_notificado_hoy(
        self, documento_id, canal: CanalNotificacion, destinatario: str
    ) -> bool:
        hoy_inicio = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        stmt = select(func.count()).where(
            and_(
                Notificacion.documento_id == documento_id,
                Notificacion.canal == canal,
                Notificacion.destinatario == destinatario,
                Notificacion.enviado_ok == True,
                Notificacion.fecha_envio >= hoy_inicio,
            )
        )
        result = await self.db.execute(stmt)
        return (result.scalar() or 0) > 0

    async def _registrar(
        self,
        documento_id,
        canal: CanalNotificacion,
        destinatario: str,
        asunto: str | None,
        cuerpo: str,
        external_id: str | None,
        ok: bool,
        error: str | None = None,
    ) -> None:
        notif = Notificacion(
            documento_id=documento_id,
            canal=canal,
            destinatario=destinatario,
            asunto=asunto,
            cuerpo=cuerpo,
            external_id=external_id,
            enviado_ok=ok,
            error_detalle=error,
        )
        self.db.add(notif)
        await self.db.flush()

    async def _enviar_si_necesario(
        self, doc: Documento, conductor: Conductor, tenant: Tenant
    ) -> int:
        enviados = 0
        fecha_str = (
            doc.fecha_vencimiento.strftime("%d/%m/%Y")
            if doc.fecha_vencimiento
            else "sin fecha"
        )

        # ── WhatsApp al conductor ─────────────────────────────────────
        if tenant.notificar_whatsapp:
            wa_svc = self._get_wa()
            numero = conductor.telefono
            if wa_svc and numero:
                if not await self._ya_notificado_hoy(doc.id, CanalNotificacion.WHATSAPP, numero):
                    mensaje = build_mensaje_vencimiento(
                        conductor.nombre_completo,
                        doc.tipo_documento_nombre,
                        doc.dias_para_vencer,
                        fecha_str,
                    )
                    res = wa_svc.enviar(numero, mensaje)
                    await self._registrar(
                        doc.id, CanalNotificacion.WHATSAPP, numero,
                        None, mensaje, res.sid, res.ok, res.error
                    )
                    if res.ok:
                        enviados += 1

        # ── Email al conductor ────────────────────────────────────────
        if tenant.notificar_email:
            email_svc = self._get_email()
            email = conductor.email
            if email_svc and email:
                if not await self._ya_notificado_hoy(doc.id, CanalNotificacion.EMAIL, email):
                    asunto, html = build_html_vencimiento(
                        conductor.nombre_completo,
                        doc.tipo_documento_nombre,
                        doc.dias_para_vencer,
                        fecha_str,
                        tenant.nombre,
                    )
                    res = email_svc.enviar(email, asunto, html)
                    await self._registrar(
                        doc.id, CanalNotificacion.EMAIL, email,
                        asunto, html, res.message_id, res.ok, res.error
                    )
                    if res.ok:
                        enviados += 1

        # ── Notificación al admin del tenant ──────────────────────────
        # El admin recibe un resumen por email (una vez por documento alertado, no por conductor)
        if tenant.notificar_email and tenant.admin_email:
            email_svc = self._get_email()
            admin_email = tenant.admin_email
            if email_svc and not await self._ya_notificado_hoy(
                doc.id, CanalNotificacion.EMAIL, admin_email
            ):
                asunto_admin = f"[Admin] {doc.tipo_documento_nombre} — {conductor.nombre_completo}"
                _, html = build_html_vencimiento(
                    conductor.nombre_completo,
                    doc.tipo_documento_nombre,
                    doc.dias_para_vencer,
                    fecha_str,
                    tenant.nombre,
                )
                res = email_svc.enviar(admin_email, asunto_admin, html)
                await self._registrar(
                    doc.id, CanalNotificacion.EMAIL, admin_email,
                    asunto_admin, html, res.message_id, res.ok, res.error
                )
                if res.ok:
                    enviados += 1

        if tenant.notificar_whatsapp and tenant.admin_whatsapp:
            wa_svc = self._get_wa()
            admin_wa = tenant.admin_whatsapp
            if wa_svc and not await self._ya_notificado_hoy(
                doc.id, CanalNotificacion.WHATSAPP, admin_wa
            ):
                mensaje_admin = (
                    f"[Admin] {conductor.nombre_completo} — "
                    + build_mensaje_vencimiento(
                        conductor.nombre_completo,
                        doc.tipo_documento_nombre,
                        doc.dias_para_vencer,
                        fecha_str,
                    )
                )
                res = wa_svc.enviar(admin_wa, mensaje_admin)
                await self._registrar(
                    doc.id, CanalNotificacion.WHATSAPP, admin_wa,
                    None, mensaje_admin, res.sid, res.ok, res.error
                )
                if res.ok:
                    enviados += 1

        return enviados
