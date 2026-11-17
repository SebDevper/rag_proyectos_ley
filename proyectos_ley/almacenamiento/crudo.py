"""Almacén de archivos crudos: los XML y PDF descargados, fuente de verdad del proyecto.

Las claves usan `/` como separador (p. ej. `camara/proyectos/18882-25/ficha.xml`),
igual que las claves de objetos en R2. Así la implementación para Cloudflare puede
reemplazar a la local sin cambiar el resto del código.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol


class AlmacenCrudo(Protocol):
    def existe(self, clave: str) -> bool: ...

    def leer(self, clave: str) -> bytes: ...

    def guardar(self, clave: str, contenido: bytes) -> None: ...

    def listar(self, prefijo: str = "") -> Iterator[str]:
        """Claves que empiezan con `prefijo`, en orden alfabético."""
        ...


class AlmacenCrudoLocal:
    """Guarda cada clave como un archivo bajo un directorio raíz."""

    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz.resolve()

    def _ruta(self, clave: str) -> Path:
        ruta = (self.raiz / clave).resolve()
        if not ruta.is_relative_to(self.raiz) or ruta == self.raiz:
            raise ValueError(f"Clave fuera del almacén: {clave!r}")
        return ruta

    def existe(self, clave: str) -> bool:
        return self._ruta(clave).is_file()

    def leer(self, clave: str) -> bytes:
        return self._ruta(clave).read_bytes()

    def guardar(self, clave: str, contenido: bytes) -> None:
        ruta = self._ruta(clave)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        # Escritura atómica: un corte a mitad de camino no deja un archivo truncado
        # que después se confunda con uno ya descargado.
        temporal = ruta.with_name(ruta.name + ".tmp")
        temporal.write_bytes(contenido)
        os.replace(temporal, ruta)

    def listar(self, prefijo: str = "") -> Iterator[str]:
        if not self.raiz.is_dir():
            return
        for ruta in sorted(self.raiz.rglob("*")):
            if not ruta.is_file() or ruta.name.endswith(".tmp"):
                continue
            clave = ruta.relative_to(self.raiz).as_posix()
            if clave.startswith(prefijo):
                yield clave
