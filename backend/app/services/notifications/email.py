"""
Email via SendGrid.
Soporta destinatario conductor y/o administrador de flota.
"""
import logging
from dataclasses import dataclass

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, From, Subject, HtmlContent

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    ok: bool
    message_id: str | None = None
    error: str | None = None


class EmailService:
    def __init__(self) -> None:
        s = get_settings()
        self._client = SendGridAPIClient(s.SENDGRID_API_KEY)
        self._from_email = s.SENDGRID_FROM_EMAIL
        self._from_name = s.SENDGRID_FROM_NAME

    def enviar(self, destinatario: str, asunto: str, html: str) -> EmailResult:
        try:
            message = Mail(
                from_email=From(self._from_email, self._from_name),
                to_emails=To(destinatario),
                subject=Subject(asunto),
                html_content=HtmlContent(html),
            )
            response = self._client.send(message)
            msg_id = response.headers.get("X-Message-Id")
            logger.info("Email enviado a %s, status=%s", destinatario, response.status_code)
            return EmailResult(ok=response.status_code in (200, 201, 202), message_id=msg_id)
        except Exception as exc:
            logger.error("Email falló para %s: %s", destinatario, exc)
            return EmailResult(ok=False, error=str(exc))


def build_html_vencimiento(
    nombre_conductor: str,
    tipo_documento: str,
    dias_para_vencer: int | None,
    fecha_vencimiento: str,
    tenant_nombre: str,
) -> tuple[str, str]:
    """Retorna (asunto, html)."""
    if dias_para_vencer is not None and dias_para_vencer < 0:
        emoji = "🔴"
        estado_texto = f"VENCIDO hace {abs(dias_para_vencer)} día(s)"
        color = "#dc2626"
    elif dias_para_vencer == 0:
        emoji = "🔴"
        estado_texto = "VENCE HOY"
        color = "#dc2626"
    else:
        emoji = "🟡"
        estado_texto = f"Vence en {dias_para_vencer} día(s)"
        color = "#d97706"

    asunto = f"{emoji} Documento por vencer: {tipo_documento} — {nombre_conductor}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: #1e293b; padding: 20px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 22px;">🚛 Zuvra Compliance</h1>
        <p style="color: #94a3b8; margin: 4px 0 0;">{tenant_nombre}</p>
      </div>
      <div style="border: 1px solid #e2e8f0; border-top: none; padding: 24px; border-radius: 0 0 8px 8px;">
        <div style="background: {color}15; border-left: 4px solid {color}; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px;">
          <strong style="color: {color}; font-size: 16px;">{estado_texto}</strong>
        </div>
        <p style="color: #374151; font-size: 15px;">
          Hola <strong>{nombre_conductor}</strong>,<br><br>
          Tu documento <strong>{tipo_documento}</strong> requiere atención:
        </p>
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
          <tr style="background: #f8fafc;">
            <td style="padding: 10px; border: 1px solid #e2e8f0; font-weight: bold; width: 50%;">Tipo de documento</td>
            <td style="padding: 10px; border: 1px solid #e2e8f0;">{tipo_documento}</td>
          </tr>
          <tr>
            <td style="padding: 10px; border: 1px solid #e2e8f0; font-weight: bold;">Fecha de vencimiento</td>
            <td style="padding: 10px; border: 1px solid #e2e8f0; color: {color}; font-weight: bold;">{fecha_vencimiento}</td>
          </tr>
          <tr style="background: #f8fafc;">
            <td style="padding: 10px; border: 1px solid #e2e8f0; font-weight: bold;">Estado</td>
            <td style="padding: 10px; border: 1px solid #e2e8f0; color: {color}; font-weight: bold;">{estado_texto}</td>
          </tr>
        </table>
        <p style="color: #6b7280; font-size: 13px; margin-top: 24px;">
          Por favor, actualizá tu documentación a la brevedad para mantener tu habilitación como conductor.
        </p>
      </div>
      <p style="color: #9ca3af; font-size: 11px; text-align: center; margin-top: 16px;">
        Zuvra Compliance · Plataforma de gestión documental para flotas
      </p>
    </body>
    </html>
    """
    return asunto, html
