"""Acceso a la base relacional detrás de una interfaz mínima.

La interfaz calza con lo que ofrece Cloudflare D1: ejecutar un lote de sentencias
de forma atómica y hacer consultas. La implementación local usa SQLite.
"""

from __future__ import annotations

import sqlite3
from importlib.resources import files
from pathlib import Path
from typing import Any, Protocol

Sentencia = tuple[str, tuple[Any, ...]]


class BaseDatos(Protocol):
    def aplicar_esquema(self) -> None: ...

    def ejecutar_lote(self, sentencias: list[Sentencia]) -> None:
        """Ejecuta todas las sentencias en una transacción: o todas o ninguna."""
        ...

    def consultar(self, sql: str, parametros: tuple[Any, ...] = ()) -> list[dict[str, Any]]: ...


def leer_esquema() -> str:
    return files("proyectos_ley.db").joinpath("esquema.sql").read_text(encoding="utf-8")


class BaseDatosSQLite:
    def __init__(self, ruta: Path | str) -> None:
        if ruta != ":memory:":
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        self._conexion = sqlite3.connect(ruta)
        self._conexion.row_factory = sqlite3.Row
        # D1 aplica las claves foráneas por defecto; SQLite requiere activarlas.
        self._conexion.execute("PRAGMA foreign_keys = ON")

    def aplicar_esquema(self) -> None:
        self._conexion.executescript(leer_esquema())

    def ejecutar_lote(self, sentencias: list[Sentencia]) -> None:
        with self._conexion:
            for sql, parametros in sentencias:
                self._conexion.execute(sql, parametros)

    def consultar(self, sql: str, parametros: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        return [dict(fila) for fila in self._conexion.execute(sql, parametros)]

    def cerrar(self) -> None:
        self._conexion.close()
