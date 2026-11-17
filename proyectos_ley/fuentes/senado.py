"""Servicio `tramitacion.php` del Senado: etapa, estado y trámites de un proyecto."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date

from proyectos_ley.fuentes.xml import fecha_dmy, texto

# Respuesta HTML (con HTTP 200) cuando el boletín no existe en el Senado
_NO_EXISTE = "No existe el n&uacute;mero de bolet&iacute;n"


def numero_boletin(boletin: str) -> str:
    """El servicio espera el número sin el sufijo de comisión: `18882-25` → `18882`.

    Con el sufijo responde "No existe el número de boletín" para los proyectos recientes.
    """
    return boletin.split("-")[0]


@dataclass(frozen=True)
class Tramite:
    orden: int
    fecha: date | None
    sesion: str | None
    descripcion: str | None
    etapa: str | None
    camara: str | None


@dataclass(frozen=True)
class Tramitacion:
    boletin: str
    etapa: str | None
    subetapa: str | None
    estado: str | None
    urgencia_actual: str | None
    ley_numero: str | None
    fecha_diario_oficial: date | None
    url_documento: str | None
    tramites: list[Tramite] = field(default_factory=list)


class RespuestaInvalida(ValueError):
    """La respuesta del servicio no tiene la estructura esperada."""


def _sin_barra(valor: str | None) -> str | None:
    """El Senado usa `/` como valor vacío (p. ej. en sesión o subetapa)."""
    if valor is None or valor.strip(" /") == "":
        return None
    return valor


def parsear_tramitacion(contenido: bytes) -> Tramitacion | None:
    """`None` si el Senado responde que el boletín no existe."""
    xml = contenido.decode("utf-8")
    if _NO_EXISTE in xml and "<proyecto>" not in xml:
        return None
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError as error:
        raise RespuestaInvalida(f"XML inválido: {error}") from error
    proyecto = raiz.find("proyecto")
    descripcion = proyecto.find("descripcion") if proyecto is not None else None
    boletin = texto(descripcion, "boletin")
    if proyecto is None or boletin is None:
        raise RespuestaInvalida("Respuesta sin <proyecto><descripcion><boletin>")
    tramites = [
        Tramite(
            orden=orden,
            fecha=fecha_dmy(texto(t, "FECHA")),
            sesion=_sin_barra(texto(t, "SESION")),
            descripcion=texto(t, "DESCRIPCIONTRAMITE"),
            etapa=texto(t, "ETAPDESCRIPCION"),
            camara=texto(t, "CAMARATRAMITE"),
        )
        for orden, t in enumerate(proyecto.findall("tramitacion/tramite"), start=1)
    ]
    return Tramitacion(
        boletin=boletin,
        etapa=texto(descripcion, "etapa"),
        subetapa=_sin_barra(texto(descripcion, "subetapa")),
        estado=texto(descripcion, "estado"),
        urgencia_actual=texto(descripcion, "urgencia_actual"),
        ley_numero=texto(descripcion, "leynro"),
        fecha_diario_oficial=fecha_dmy(texto(descripcion, "diariooficial")),
        url_documento=texto(descripcion, "link_mensaje_mocion"),
        tramites=tramites,
    )
