"""Claves de los archivos en el almacén crudo (rutas bajo data/raw o claves de R2)."""

from __future__ import annotations


def listado(tipo_iniciativa: str, anno: int) -> str:
    nombre = {"Moción": "mociones", "Mensaje": "mensajes"}[tipo_iniciativa]
    return f"camara/listados/{nombre}_{anno}.xml"


def prefijo_proyecto(boletin: str) -> str:
    return f"camara/proyectos/{boletin}/"


def ficha(boletin: str) -> str:
    return f"{prefijo_proyecto(boletin)}ficha.xml"


def prefijo_documento_ingreso(boletin: str) -> str:
    """El documento se guarda decodificado; la extensión depende de su ContentType."""
    return f"{prefijo_proyecto(boletin)}documento_ingreso."


def documento_ingreso(boletin: str, extension: str) -> str:
    return f"{prefijo_documento_ingreso(boletin)}{extension}"


def tramitacion_senado(boletin: str) -> str:
    return f"senado/tramitacion/{boletin}.xml"


def boletin_desde_ficha(clave: str) -> str | None:
    """`camara/proyectos/18882-25/ficha.xml` → `18882-25`."""
    partes = clave.split("/")
    if len(partes) == 4 and partes[:2] == ["camara", "proyectos"] and partes[3] == "ficha.xml":
        return partes[2]
    return None
