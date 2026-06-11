"""
WhatsApp via Twilio Messaging API.
Usa WhatsApp Sandbox para desarrollo, número aprobado en producción.
"""
import logging
from dataclasses import dataclass

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppResult:
    ok: bool
    sid: str | None = None
    error: str | None = None


class WhatsAppService:
    def __init__(self) -> None:
        s = get_settings()
        self._client = Client(s.TWILIO_ACCOUNT_SID, s.TWILIO_AUTH_TOKEN)
        self._from = s.TWILIO_WHATSAPP_FROM

    def _normalize_to(self, numero: str) -> str:
        """Asegura formato whatsapp:+549..."""
        numero = numero.strip().replace(" ", "")
        if not numero.startswith("whatsapp:"):
            if not numero.startswith("+"):
                numero = "+" + numero
            numero = f"whatsapp:{numero}"
        return numero

    def enviar(self, numero: str, mensaje: str) -> WhatsAppResult:
        try:
            msg = self._client.messages.create(
                from_=self._from,
                to=self._normalize_to(numero),
                body=mensaje,
            )
            logger.info("WhatsApp enviado a %s, SID=%s", numero, msg.sid)
            return WhatsAppResult(ok=True, sid=msg.sid)
        except TwilioRestException as exc:
            logger.error("WhatsApp falló para %s: %s", numero, exc)
            return WhatsAppResult(ok=False, error=str(exc))


def build_mensaje_vencimiento(
    nombre_conductor: str,
    tipo_documento: str,
    dias_para_vencer: int | None,
    fecha_vencimiento: str,
) -> str:
    if dias_para_vencer is not None and dias_para_vencer < 0:
        urgencia = f"⚠️ *VENCIDO* hace {abs(dias_para_vencer)} día(s)"
    elif dias_para_vencer == 0:
        urgencia = "🔴 *VENCE HOY*"
    else:
        urgencia = f"🟡 Vence en *{dias_para_vencer} día(s)*"

    return (
        f"Hola {nombre_conductor} 👋\n\n"
        f"Tu documento *{tipo_documento}* está {urgencia}.\n"
        f"📅 Fecha de vencimiento: *{fecha_vencimiento}*\n\n"
        f"Por favor actualizá tu documentación a la brevedad.\n"
        f"— Zuvra Compliance 🚛"
    )
