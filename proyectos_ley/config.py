"""Configuración leída desde variables de entorno, con un archivo `.env` opcional.

No hay rutas, endpoints ni claves en el código: todo viene del entorno para que el
mismo programa corra en local o apuntando a Cloudflare.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path


class ConfiguracionError(RuntimeError):
    """Falta una variable de entorno o tiene un valor inválido."""


def cargar_dotenv(ruta: Path = Path(".env")) -> None:
    """Carga líneas `CLAVE=valor` de un `.env` sin pisar variables ya definidas."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip("\"'"))


def _requerida(nombre: str) -> str:
    valor = os.environ.get(nombre, "").strip()
    if not valor:
        raise ConfiguracionError(f"Falta la variable de entorno {nombre} (ver .env.example)")
    return valor


def _fecha(nombre: str) -> date | None:
    valor = os.environ.get(nombre, "").strip()
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError as error:
        raise ConfiguracionError(f"{nombre} debe tener formato AAAA-MM-DD: {valor!r}") from error


@dataclass(frozen=True)
class Config:
    dir_crudo: Path
    ruta_db: Path
    camara_ws_url: str
    senado_ws_url: str
    user_agent: str
    pausa_min: float
    pausa_max: float
    fecha_desde: date | None

    @classmethod
    def desde_entorno(cls) -> Config:
        cargar_dotenv()
        config = cls(
            dir_crudo=Path(_requerida("DIR_CRUDO")),
            ruta_db=Path(_requerida("RUTA_DB")),
            camara_ws_url=_requerida("CAMARA_WS_URL"),
            senado_ws_url=_requerida("SENADO_WS_URL"),
            user_agent=_requerida("USER_AGENT"),
            pausa_min=float(os.environ.get("PAUSA_MIN_SEGUNDOS", "1")),
            pausa_max=float(os.environ.get("PAUSA_MAX_SEGUNDOS", "2")),
            fecha_desde=_fecha("FECHA_DESDE"),
        )
        if not 0 < config.pausa_min <= config.pausa_max:
            raise ConfiguracionError("Se requiere 0 < PAUSA_MIN_SEGUNDOS <= PAUSA_MAX_SEGUNDOS")
        return config
