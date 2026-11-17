-- Esquema de la base relacional. SQLite estándar, compatible con Cloudflare D1.
-- Se regenera por completo desde los archivos crudos (python -m proyectos_ley.ingesta.cargar).
-- Fechas en formato ISO 'AAAA-MM-DD'; booleanos como 0/1.

-- Un proyecto por boletín. La identidad y los datos de ingreso vienen de la ficha
-- de la Cámara; la etapa, el estado y la urgencia, de la tramitación del Senado.
CREATE TABLE IF NOT EXISTS proyectos (
    boletin              TEXT PRIMARY KEY,          -- '18882-25'
    camara_id            INTEGER NOT NULL,          -- Id en la Cámara (el Senado lo usa como iddocto)
    titulo               TEXT NOT NULL,
    fecha_ingreso        TEXT NOT NULL,
    tipo_iniciativa      TEXT NOT NULL,             -- 'Mensaje' (Ejecutivo) o 'Moción' (parlamentaria)
    camara_origen        TEXT,
    admisible            INTEGER,
    etapa                TEXT,
    subetapa             TEXT,
    estado               TEXT,
    urgencia_actual      TEXT,
    ley_numero           TEXT,
    fecha_diario_oficial TEXT,
    url_documento_senado TEXT,
    actualizado_en       TEXT NOT NULL              -- momento de la última carga (UTC)
);

CREATE INDEX IF NOT EXISTS idx_proyectos_fecha_ingreso ON proyectos (fecha_ingreso);

-- Parlamentarios autores de una moción
CREATE TABLE IF NOT EXISTS autores (
    boletin          TEXT NOT NULL REFERENCES proyectos (boletin) ON DELETE CASCADE,
    parlamentario_id INTEGER NOT NULL,
    nombre           TEXT NOT NULL,
    camara           TEXT NOT NULL,
    PRIMARY KEY (boletin, parlamentario_id)
);

-- Ministerios que patrocinan un mensaje del Ejecutivo
CREATE TABLE IF NOT EXISTS ministerios_patrocinantes (
    boletin       TEXT NOT NULL REFERENCES proyectos (boletin) ON DELETE CASCADE,
    ministerio_id INTEGER NOT NULL,
    nombre        TEXT NOT NULL,
    PRIMARY KEY (boletin, ministerio_id)
);

-- Trámites del proyecto, en el orden en que los informa el Senado
CREATE TABLE IF NOT EXISTS tramites (
    boletin     TEXT NOT NULL REFERENCES proyectos (boletin) ON DELETE CASCADE,
    orden       INTEGER NOT NULL,
    fecha       TEXT,
    sesion      TEXT,
    descripcion TEXT,
    etapa       TEXT,
    camara      TEXT,
    PRIMARY KEY (boletin, orden)
);

CREATE INDEX IF NOT EXISTS idx_tramites_fecha ON tramites (fecha);

-- Archivos crudos asociados a un proyecto (p. ej. el texto de ingreso en PDF)
CREATE TABLE IF NOT EXISTS documentos (
    boletin      TEXT NOT NULL REFERENCES proyectos (boletin) ON DELETE CASCADE,
    tipo         TEXT NOT NULL,                     -- 'ingreso'
    clave_crudo  TEXT NOT NULL,                     -- clave en el almacén crudo (data/raw o R2)
    content_type TEXT NOT NULL,
    bytes        INTEGER NOT NULL,
    sha256       TEXT NOT NULL,
    PRIMARY KEY (boletin, tipo)
);
