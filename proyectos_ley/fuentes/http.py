"""Cliente HTTP de descarga responsable.

Una solicitud a la vez, con una pausa aleatoria entre solicitudes y reintentos con
espera creciente ante errores temporales (5xx o problemas de red).
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)


class ClienteHttp:
    def __init__(
        self,
        user_agent: str,
        pausa_min: float,
        pausa_max: float,
        timeout: float = 60,
        reintentos: int = 3,
        espera_reintento: float = 5,
        dormir: Callable[[float], None] = time.sleep,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        self.user_agent = user_agent
        self.pausa_min = pausa_min
        self.pausa_max = pausa_max
        self.timeout = timeout
        self.reintentos = reintentos
        self.espera_reintento = espera_reintento
        self._dormir = dormir
        self._reloj = reloj
        self._fin_ultima: float | None = None
        self.solicitudes = 0

    def get(self, url: str, params: dict[str, str | int] | None = None) -> bytes:
        if params:
            url = f"{url}?{urlencode(params)}"
        for intento in range(1, self.reintentos + 1):
            self._esperar_turno()
            try:
                return self._solicitar(url)
            except HTTPError as error:
                if error.code < 500 or intento == self.reintentos:
                    raise
                motivo = f"HTTP {error.code}"
            except (URLError, TimeoutError) as error:
                if intento == self.reintentos:
                    raise
                motivo = str(error)
            espera = self.espera_reintento * 3 ** (intento - 1)
            log.warning("Falló %s (%s); reintento en %.0f s", url, motivo, espera)
            self._dormir(espera)
        raise AssertionError("inalcanzable")

    def _solicitar(self, url: str) -> bytes:
        self.solicitudes += 1
        try:
            solicitud = Request(url, headers={"User-Agent": self.user_agent})
            with urlopen(solicitud, timeout=self.timeout) as respuesta:
                return respuesta.read()
        finally:
            self._fin_ultima = self._reloj()

    def _esperar_turno(self) -> None:
        if self._fin_ultima is None:
            return
        pausa = random.uniform(self.pausa_min, self.pausa_max)
        restante = pausa - (self._reloj() - self._fin_ultima)
        if restante > 0:
            self._dormir(restante)
