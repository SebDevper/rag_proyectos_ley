"""Servicio `WSLegislativo.asmx` de la Cámara: listados, ficha y documento de ingreso."""

from __future__ import annotations

import base64
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date

from proyectos_ley.fuentes.xml import fecha_iso, texto

NS = {"c": "http://opendata.camara.cl/camaradiputados/v1"}

# Operación del listado anual según el tipo de iniciativa
OPERACIONES_LISTADO = {
    "Moción": "retornarMocionesXAnno",
    "Mensaje": "retornarMensajesXAnno",
}
OPERACION_FICHA = "retornarProyectoLey"
OPERACION_DOCUMENTO = "retornarDocumentoIngresoProyectoLey"

# Elemento hijo de <ParlamentarioAutor> → cámara del autor
_CAMARA_AUTOR = {"Senador": "Senado", "Diputado": "Cámara de Diputados"}

# Extensión del archivo según el ContentType del documento de ingreso
EXTENSIONES = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


def url_operacion(base: str, operacion: str) -> str:
    return f"{base.rstrip('/')}/{operacion}"


@dataclass(frozen=True)
class Proyecto:
    camara_id: int
    boletin: str
    titulo: str
    fecha_ingreso: date
    tipo_iniciativa: str
    camara_origen: str | None
    admisible: bool | None


@dataclass(frozen=True)
class Autor:
    parlamentario_id: int
    nombre: str
    camara: str


@dataclass(frozen=True)
class Ministerio:
    ministerio_id: int
    nombre: str


@dataclass(frozen=True)
class Ficha:
    proyecto: Proyecto
    autores: list[Autor] = field(default_factory=list)
    ministerios: list[Ministerio] = field(default_factory=list)


@dataclass(frozen=True)
class Documento:
    nombre: str | None
    content_type: str
    contenido: bytes

    @property
    def extension(self) -> str:
        return EXTENSIONES.get(self.content_type, "bin")


class RespuestaInvalida(ValueError):
    """La respuesta del servicio no tiene la estructura esperada."""


def _raiz(xml: bytes, etiqueta: str) -> ET.Element:
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError as error:
        raise RespuestaInvalida(f"XML inválido: {error}") from error
    if raiz.tag != f"{{{NS['c']}}}{etiqueta}":
        raise RespuestaInvalida(f"Se esperaba <{etiqueta}> y llegó <{raiz.tag}>")
    return raiz


def _proyecto(elemento: ET.Element) -> Proyecto:
    boletin = texto(elemento, "c:NumeroBoletin", NS)
    fecha = fecha_iso(texto(elemento, "c:FechaIngreso", NS))
    titulo = texto(elemento, "c:Nombre", NS)
    tipo = texto(elemento, "c:TipoIniciativa", NS)
    id_ = texto(elemento, "c:Id", NS)
    if not (boletin and fecha and titulo and tipo and id_):
        raise RespuestaInvalida("Proyecto sin boletín, fecha, título, tipo o Id")
    admisible = texto(elemento, "c:Admisible", NS)
    return Proyecto(
        camara_id=int(id_),
        boletin=boletin,
        titulo=titulo,
        fecha_ingreso=fecha,
        tipo_iniciativa=tipo,
        camara_origen=texto(elemento, "c:CamaraOrigen", NS),
        admisible=None if admisible is None else admisible == "true",
    )


def parsear_listado(xml: bytes) -> list[Proyecto]:
    raiz = _raiz(xml, "ProyectosLeyColeccion")
    return [_proyecto(e) for e in raiz.findall("c:ProyectoLey", NS)]


def parsear_ficha(xml: bytes) -> Ficha:
    raiz = _raiz(xml, "ProyectoLey")
    autores = []
    for autor in raiz.findall("c:Autores/c:ParlamentarioAutor", NS):
        for persona in autor:
            etiqueta = persona.tag.split("}")[-1]
            if etiqueta == "Orden":
                continue
            nombre = " ".join(
                parte
                for parte in (
                    texto(persona, "c:Nombre", NS),
                    texto(persona, "c:ApellidoPaterno", NS),
                    texto(persona, "c:ApellidoMaterno", NS),
                )
                if parte
            )
            autores.append(
                Autor(
                    parlamentario_id=int(texto(persona, "c:Id", NS) or 0),
                    nombre=nombre,
                    camara=_CAMARA_AUTOR.get(etiqueta, etiqueta),
                )
            )
    ministerios = [
        Ministerio(ministerio_id=int(texto(m, "c:Id", NS) or 0), nombre=texto(m, "c:Nombre", NS) or "")
        for m in raiz.findall("c:MinisteriosPatrocinantes/c:Ministerio", NS)
    ]
    return Ficha(proyecto=_proyecto(raiz), autores=autores, ministerios=ministerios)


def parsear_documento(xml: bytes) -> Documento | None:
    """Decodifica el archivo en base64; `None` si el servicio no lo trae."""
    raiz = _raiz(xml, "Documento")
    archivo = raiz.findtext("c:Archivo", namespaces=NS)
    if not archivo or not archivo.strip():
        return None
    return Documento(
        nombre=texto(raiz, "c:Nombre", NS),
        content_type=texto(raiz, "c:ContentType", NS) or "application/octet-stream",
        contenido=base64.b64decode(archivo),
    )
