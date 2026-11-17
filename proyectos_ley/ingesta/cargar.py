"""Carga los archivos crudos a la base relacional.

No usa la red: lee solo el almacén crudo, así que la base se puede borrar y
regenerar en cualquier momento.

Uso:
    python -m proyectos_ley.ingesta.cargar
"""

from __future__ import annotations

import argparse
import hashlib
import logging
from dataclasses import dataclass, field

from proyectos_ley.almacenamiento.crudo import AlmacenCrudo, AlmacenCrudoLocal
from proyectos_ley.config import Config, ConfiguracionError
from proyectos_ley.db.base import BaseDatos, BaseDatosSQLite
from proyectos_ley.db.repositorio import RegistroDocumento, guardar_proyecto
from proyectos_ley.fuentes import camara, senado
from proyectos_ley.ingesta import claves

log = logging.getLogger(__name__)

_CONTENT_TYPES = {extension: tipo for tipo, extension in camara.EXTENSIONES.items()}


@dataclass
class ResumenCarga:
    cargados: int = 0
    sin_tramitacion: int = 0
    sin_documento: int = 0
    errores: dict[str, str] = field(default_factory=dict)


def _documentos(almacen: AlmacenCrudo, boletin: str) -> list[RegistroDocumento]:
    registros = []
    for clave in almacen.listar(claves.prefijo_documento_ingreso(boletin)):
        contenido = almacen.leer(clave)
        extension = clave.rsplit(".", 1)[-1]
        registros.append(
            RegistroDocumento(
                tipo="ingreso",
                clave_crudo=clave,
                content_type=_CONTENT_TYPES.get(extension, "application/octet-stream"),
                bytes=len(contenido),
                sha256=hashlib.sha256(contenido).hexdigest(),
            )
        )
    return registros[:1]


def cargar(almacen: AlmacenCrudo, db: BaseDatos) -> ResumenCarga:
    db.aplicar_esquema()
    resumen = ResumenCarga()
    for clave in almacen.listar("camara/proyectos/"):
        boletin = claves.boletin_desde_ficha(clave)
        if boletin is None:
            continue
        try:
            ficha = camara.parsear_ficha(almacen.leer(clave))
            clave_senado = claves.tramitacion_senado(boletin)
            tramitacion = (
                senado.parsear_tramitacion(almacen.leer(clave_senado)) if almacen.existe(clave_senado) else None
            )
            documentos = _documentos(almacen, boletin)
            guardar_proyecto(db, ficha, tramitacion, documentos)
        except Exception as error:
            log.error("%s: %s", boletin, error)
            resumen.errores[boletin] = str(error)
            continue
        resumen.cargados += 1
        resumen.sin_tramitacion += tramitacion is None
        resumen.sin_documento += not documentos
    return resumen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    try:
        config = Config.desde_entorno()
    except ConfiguracionError as error:
        parser.error(str(error))

    db = BaseDatosSQLite(config.ruta_db)
    try:
        resumen = cargar(AlmacenCrudoLocal(config.dir_crudo), db)
    finally:
        db.cerrar()
    log.info(
        "Listo: %d proyectos cargados en %s (%d sin tramitación, %d sin documento)",
        resumen.cargados,
        config.ruta_db,
        resumen.sin_tramitacion,
        resumen.sin_documento,
    )
    return 1 if resumen.errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
