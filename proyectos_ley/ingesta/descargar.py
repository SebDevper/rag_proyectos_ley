"""Descarga los proyectos ingresados desde una fecha y guarda las respuestas crudas.

Por cada boletín se obtienen tres archivos:

1. Ficha de la Cámara (metadatos, autores, ministerios).
2. Documento de ingreso de la Cámara (PDF, decodificado desde base64).
3. Tramitación del Senado (etapa, estado y trámites).

La ficha y el documento no cambian: si ya están en el almacén no se vuelven a pedir.
La tramitación sí cambia; se actualiza solo con `--actualizar-tramitacion`.
Los listados anuales se piden en cada corrida porque son el índice de lo nuevo.

Uso:
    python -m proyectos_ley.ingesta.descargar [--desde AAAA-MM-DD] [--limite N]
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from proyectos_ley.almacenamiento.crudo import AlmacenCrudo, AlmacenCrudoLocal
from proyectos_ley.config import Config, ConfiguracionError
from proyectos_ley.fuentes import camara, senado
from proyectos_ley.fuentes.http import ClienteHttp
from proyectos_ley.ingesta import claves

log = logging.getLogger(__name__)


class Cliente(Protocol):
    """Lo que la descarga necesita de un cliente HTTP (permite usar uno falso en tests)."""

    def get(self, url: str, params: dict[str, str | int] | None = None) -> bytes: ...


@dataclass
class Resumen:
    proyectos: int = 0
    descargados: int = 0
    en_cache: int = 0
    sin_documento: list[str] = field(default_factory=list)
    sin_tramitacion: list[str] = field(default_factory=list)
    errores: dict[str, str] = field(default_factory=dict)


def listar_proyectos(
    cliente: Cliente, almacen: AlmacenCrudo, config: Config, desde: date, hasta: date
) -> list[camara.Proyecto]:
    """Mociones y mensajes ingresados desde `desde`, ordenados por fecha y boletín."""
    proyectos: dict[str, camara.Proyecto] = {}
    for anno in range(desde.year, hasta.year + 1):
        for tipo, operacion in camara.OPERACIONES_LISTADO.items():
            xml = cliente.get(camara.url_operacion(config.camara_ws_url, operacion), {"prmAnno": anno})
            listado = camara.parsear_listado(xml)
            almacen.guardar(claves.listado(tipo, anno), xml)
            log.info("Listado %s %d: %d proyectos", tipo, anno, len(listado))
            proyectos.update({p.boletin: p for p in listado if p.fecha_ingreso >= desde})
    return sorted(proyectos.values(), key=lambda p: (p.fecha_ingreso, p.boletin))


def descargar_proyecto(
    cliente: Cliente,
    almacen: AlmacenCrudo,
    config: Config,
    boletin: str,
    resumen: Resumen,
    actualizar_tramitacion: bool = False,
) -> bool:
    """Descarga lo que falte de un boletín. Devuelve True si hizo alguna solicitud."""
    descargo = False

    clave_ficha = claves.ficha(boletin)
    if not almacen.existe(clave_ficha):
        url = camara.url_operacion(config.camara_ws_url, camara.OPERACION_FICHA)
        xml = cliente.get(url, {"prmNumeroBoletin": boletin})
        camara.parsear_ficha(xml)  # valida antes de guardar
        almacen.guardar(clave_ficha, xml)
        descargo = True

    if not any(almacen.listar(claves.prefijo_documento_ingreso(boletin))):
        url = camara.url_operacion(config.camara_ws_url, camara.OPERACION_DOCUMENTO)
        documento = camara.parsear_documento(cliente.get(url, {"prmNumeroBoletin": boletin}))
        descargo = True
        if documento is None:
            log.warning("%s: la Cámara no entrega documento de ingreso (se reintentará)", boletin)
            resumen.sin_documento.append(boletin)
        else:
            almacen.guardar(claves.documento_ingreso(boletin, documento.extension), documento.contenido)

    clave_senado = claves.tramitacion_senado(boletin)
    if actualizar_tramitacion or not almacen.existe(clave_senado):
        contenido = cliente.get(config.senado_ws_url, {"boletin": senado.numero_boletin(boletin)})
        tramitacion = senado.parsear_tramitacion(contenido)
        descargo = True
        if tramitacion is None:
            log.warning("%s: el Senado aún no tiene el boletín (se reintentará)", boletin)
            resumen.sin_tramitacion.append(boletin)
        elif tramitacion.boletin != boletin:
            raise senado.RespuestaInvalida(f"El Senado devolvió {tramitacion.boletin} en vez de {boletin}")
        else:
            almacen.guardar(clave_senado, contenido)

    return descargo


def descargar(
    cliente: Cliente,
    almacen: AlmacenCrudo,
    config: Config,
    desde: date,
    hasta: date | None = None,
    limite: int | None = None,
    actualizar_tramitacion: bool = False,
) -> Resumen:
    proyectos = listar_proyectos(cliente, almacen, config, desde, hasta or date.today())
    if limite is not None:
        proyectos = proyectos[:limite]
    resumen = Resumen(proyectos=len(proyectos))
    log.info("%d proyectos ingresados desde %s", len(proyectos), desde.isoformat())
    for i, proyecto in enumerate(proyectos, start=1):
        try:
            if descargar_proyecto(cliente, almacen, config, proyecto.boletin, resumen, actualizar_tramitacion):
                resumen.descargados += 1
                log.info("[%d/%d] %s descargado", i, len(proyectos), proyecto.boletin)
            else:
                resumen.en_cache += 1
        except Exception as error:  # un boletín con problemas no detiene la descarga
            log.error("[%d/%d] %s: %s", i, len(proyectos), proyecto.boletin, error)
            resumen.errores[proyecto.boletin] = str(error)
    return resumen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--desde", type=date.fromisoformat, help="AAAA-MM-DD; por defecto FECHA_DESDE")
    parser.add_argument("--limite", type=int, help="descargar como máximo N proyectos (para pruebas)")
    parser.add_argument(
        "--actualizar-tramitacion", action="store_true", help="volver a pedir la tramitación al Senado"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    try:
        config = Config.desde_entorno()
    except ConfiguracionError as error:
        parser.error(str(error))
    desde = args.desde or config.fecha_desde
    if desde is None:
        parser.error("Indica --desde o define FECHA_DESDE")

    cliente = ClienteHttp(config.user_agent, config.pausa_min, config.pausa_max)
    resumen = descargar(
        cliente,
        AlmacenCrudoLocal(config.dir_crudo),
        config,
        desde,
        limite=args.limite,
        actualizar_tramitacion=args.actualizar_tramitacion,
    )
    log.info(
        "Listo: %d proyectos, %d descargados, %d ya estaban en caché, %d solicitudes HTTP",
        resumen.proyectos,
        resumen.descargados,
        resumen.en_cache,
        cliente.solicitudes,
    )
    if resumen.sin_documento:
        log.warning("Sin documento de ingreso: %s", ", ".join(resumen.sin_documento))
    if resumen.sin_tramitacion:
        log.warning("Sin tramitación en el Senado: %s", ", ".join(resumen.sin_tramitacion))
    if resumen.errores:
        log.error("Con errores: %s", ", ".join(resumen.errores))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
