"""Utilidades comunes para leer los XML de los servicios."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date, datetime


def texto(elemento: ET.Element | None, ruta: str, ns: dict[str, str] | None = None) -> str | None:
    """Texto de un subelemento, sin espacios sobrantes; `None` si no existe o está vacío."""
    if elemento is None:
        return None
    valor = elemento.findtext(ruta, namespaces=ns)
    if valor is None:
        return None
    valor = " ".join(valor.split())
    return valor or None


def fecha_iso(valor: str | None) -> date | None:
    """`2026-03-06T00:00:00` → date."""
    return date.fromisoformat(valor[:10]) if valor else None


def fecha_dmy(valor: str | None) -> date | None:
    """`10/11/2026` → date."""
    return datetime.strptime(valor, "%d/%m/%Y").date() if valor else None
