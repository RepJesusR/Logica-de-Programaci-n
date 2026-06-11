"""
UNIGIS MAPI SOAP Client base.

Gestiona la conexión zeep, autenticación y retry automático.
Cada instancia corresponde a un Tenant con sus propias credenciales.
"""
import logging
from functools import cached_property
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from zeep import Client, Settings as ZeepSettings
from zeep.cache import SqliteCache
from zeep.transports import Transport

logger = logging.getLogger(__name__)

_RETRY_KWARGS = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


class UnigisClient:
    """Thin wrapper sobre zeep para UNIGIS MAPI SOAP."""

    def __init__(
        self,
        wsdl_url: str,
        api_key: str,
        login: str,
        password: str,
    ) -> None:
        self.wsdl_url = wsdl_url
        self.api_key = api_key
        self.login = login
        self.password = password

    @cached_property
    def _zeep(self) -> Client:
        transport = Transport(
            cache=SqliteCache(timeout=3600),
            timeout=30,
            operation_timeout=60,
        )
        settings = ZeepSettings(strict=False, xml_huge_tree=True)
        client = Client(self.wsdl_url, transport=transport, settings=settings)
        return client

    def _auth_header(self) -> dict[str, str]:
        """Header de autenticación que UNIGIS MAPI espera en cada llamada."""
        return {
            "ApiKey": self.api_key,
            "Login": self.login,
            "Password": self.password,
        }

    @retry(**_RETRY_KWARGS)
    def call(self, operation: str, **kwargs: Any) -> Any:
        """
        Ejecuta una operación SOAP contra UNIGIS.

        Ejemplo:
            client.call("ConsultarConductor", NroDocumento="20123456")
        """
        service = self._zeep.service
        method = getattr(service, operation)
        result = method(**self._auth_header(), **kwargs)
        logger.debug("UNIGIS %s → %s", operation, result)
        return result

    @classmethod
    def from_tenant(cls, tenant: Any) -> "UnigisClient":
        """Factory que construye el cliente desde un modelo Tenant."""
        return cls(
            wsdl_url=tenant.unigis_wsdl_url,
            api_key=tenant.unigis_api_key,
            login=tenant.unigis_login,
            password=tenant.unigis_password,
        )
