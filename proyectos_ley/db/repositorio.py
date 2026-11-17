"""Traduce los datos de las fuentes a sentencias SQL sobre el esquema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from proyectos_ley.db.base import BaseDatos, Sentencia
from proyectos_ley.fuentes.camara import Ficha
from proyectos_ley.fuentes.senado import Tramitacion


@dataclass(frozen=True)
class RegistroDocumento:
    tipo: str
    clave_crudo: str
    content_type: str
    bytes: int
    sha256: str


def _iso(valor: date | None) -> str | None:
    return valor.isoformat() if valor else None


def guardar_proyecto(
    db: BaseDatos,
    ficha: Ficha,
    tramitacion: Tramitacion | None,
    documentos: list[RegistroDocumento],
) -> None:
    """Inserta o reemplaza un proyecto con todas sus filas relacionadas, de forma atómica."""
    p = ficha.proyecto
    t = tramitacion
    ahora = datetime.now(UTC).isoformat(timespec="seconds")
    sentencias: list[Sentencia] = [
        (
            """
            INSERT INTO proyectos (
                boletin, camara_id, titulo, fecha_ingreso, tipo_iniciativa, camara_origen,
                admisible, etapa, subetapa, estado, urgencia_actual, ley_numero,
                fecha_diario_oficial, url_documento_senado, actualizado_en
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (boletin) DO UPDATE SET
                camara_id = excluded.camara_id,
                titulo = excluded.titulo,
                fecha_ingreso = excluded.fecha_ingreso,
                tipo_iniciativa = excluded.tipo_iniciativa,
                camara_origen = excluded.camara_origen,
                admisible = excluded.admisible,
                etapa = excluded.etapa,
                subetapa = excluded.subetapa,
                estado = excluded.estado,
                urgencia_actual = excluded.urgencia_actual,
                ley_numero = excluded.ley_numero,
                fecha_diario_oficial = excluded.fecha_diario_oficial,
                url_documento_senado = excluded.url_documento_senado,
                actualizado_en = excluded.actualizado_en
            """,
            (
                p.boletin,
                p.camara_id,
                p.titulo,
                p.fecha_ingreso.isoformat(),
                p.tipo_iniciativa,
                p.camara_origen,
                None if p.admisible is None else int(p.admisible),
                t.etapa if t else None,
                t.subetapa if t else None,
                t.estado if t else None,
                t.urgencia_actual if t else None,
                t.ley_numero if t else None,
                _iso(t.fecha_diario_oficial) if t else None,
                t.url_documento if t else None,
                ahora,
            ),
        )
    ]
    # Las filas hijas se reemplazan completas para que la carga sea idempotente.
    for tabla in ("autores", "ministerios_patrocinantes", "tramites", "documentos"):
        sentencias.append((f"DELETE FROM {tabla} WHERE boletin = ?", (p.boletin,)))
    sentencias += [
        (
            "INSERT OR IGNORE INTO autores (boletin, parlamentario_id, nombre, camara) VALUES (?, ?, ?, ?)",
            (p.boletin, a.parlamentario_id, a.nombre, a.camara),
        )
        for a in ficha.autores
    ]
    sentencias += [
        (
            "INSERT OR IGNORE INTO ministerios_patrocinantes (boletin, ministerio_id, nombre) VALUES (?, ?, ?)",
            (p.boletin, m.ministerio_id, m.nombre),
        )
        for m in ficha.ministerios
    ]
    if t:
        sentencias += [
            (
                "INSERT INTO tramites (boletin, orden, fecha, sesion, descripcion, etapa, camara)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (p.boletin, tr.orden, _iso(tr.fecha), tr.sesion, tr.descripcion, tr.etapa, tr.camara),
            )
            for tr in t.tramites
        ]
    sentencias += [
        (
            "INSERT INTO documentos (boletin, tipo, clave_crudo, content_type, bytes, sha256)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (p.boletin, d.tipo, d.clave_crudo, d.content_type, d.bytes, d.sha256),
        )
        for d in documentos
    ]
    db.ejecutar_lote(sentencias)
