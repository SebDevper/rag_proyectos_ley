# rag_proyectos_ley

Asistente para consultar en lenguaje natural los **proyectos de ley del Congreso Nacional de Chile**: qué proponen, en qué etapa de tramitación están, quién los presentó y cómo se han votado.

> ⚠️ Proyecto en desarrollo. Herramienta informativa, **no oficial** y sin afiliación con el Congreso Nacional, la Cámara de Diputadas y Diputados, el Senado ni la Biblioteca del Congreso Nacional.

## Objetivo

Responder preguntas como:

- *"¿Qué proyectos sobre isapres se están discutiendo?"*
- *"¿En qué etapa va el proyecto de ley de patrimonio cultural?"*
- *"¿Qué propone el proyecto sobre Juan Fernández que ingresó el Ejecutivo?"*
- *"¿Cómo se votó en la Cámara el proyecto X?"*

Las respuestas incluyen siempre **citas verificables**: número de boletín, documento y trámite, con enlace a la fuente oficial. Si no hay respaldo en los documentos, el sistema lo indica.

## Fuentes de datos

Servicios web oficiales del portal de [Datos Abiertos Legislativos](https://opendata.camara.cl/) del Congreso Nacional (Cámara, Senado y BCN). El portal declara que los datos pueden usarse *"libre de trabas o restricciones como derechos de autor, licencias u otros mecanismos de control"*.

| Fuente | Datos |
|--------|-------|
| Senado | Ficha y tramitación de cada proyecto, proyectos con movimiento desde una fecha, votaciones, sesiones |
| Cámara | Mociones y mensajes por año, ficha del proyecto, **texto del proyecto (PDF)**, votaciones |
| BCN | Texto actualizado de las leyes publicadas (LeyChile) |

Detalle en [docs/fuente-de-datos.md](docs/fuente-de-datos.md) y análisis legal en [docs/legal.md](docs/legal.md).

## Alcance

| Fase | Contenido | Estado |
|------|-----------|--------|
| 1 | Proyectos ingresados desde una fecha configurable (`FECHA_DESDE`): metadatos, tramitación y texto de ingreso. Desarrollo con el último mes (~96 proyectos); evaluación y demo con el periodo legislativo actual (desde el 11-03-2026) | 🚧 Por iniciar |
| 2 | Votaciones y actualización diaria incremental | Pendiente |
| 3 | Informes de comisión, diario de sesiones, leyes publicadas (BCN) y periodos anteriores | Pendiente |

## Arquitectura (preliminar)

```
[Ingesta — Python]
  Servicios Senado/Cámara → XML y PDF crudos (data/raw)
    → extracción y limpieza del texto
    → chunking por sección del proyecto
    → embeddings → vector store
    → metadatos, tramitación, votaciones y texto (FTS5) → SQLite

[Consulta]
  pregunta → búsqueda híbrida (semántica + léxica) sobre el texto
           + consultas estructuradas sobre tramitación y votaciones
           → reranker → LLM → respuesta con citas
```

- **Local primero, portable a Cloudflare** (capa gratuita: Workers, D1, Vectorize, R2 y Workers AI). Ver [docs/despliegue.md](docs/despliegue.md).
- **Híbrido RAG + datos estructurados:** el contenido de los proyectos se busca con RAG; la etapa, las fechas y las votaciones se consultan como datos.

## Uso

Requiere Python 3.12 o superior. La ingesta usa solo la biblioteca estándar.

```bash
cp .env.example .env                              # ajustar FECHA_DESDE si hace falta
python3 -m proyectos_ley.ingesta.descargar        # servicios web → data/raw
python3 -m proyectos_ley.ingesta.cargar           # data/raw → data/proyectos.sqlite
python3 -m unittest discover -s tests -t .        # tests
```

**Descarga** (`descargar`): pide los listados anuales de la Cámara, filtra los proyectos ingresados desde `FECHA_DESDE` y, por cada boletín, guarda la ficha de la Cámara, el documento de ingreso (PDF) y la tramitación del Senado. Hace una solicitud a la vez con pausas de 1 a 2 segundos y no vuelve a pedir lo que ya está en `data/raw`. La tramitación cambia con el tiempo y se refresca con `--actualizar-tramitacion`.

**Carga** (`cargar`): lee solo `data/raw`, sin red, y llena la base SQLite ([esquema](proyectos_ley/db/esquema.sql), compatible con D1). La base se puede borrar y regenerar en cualquier momento.

```
data/raw/
├── camara/listados/{mociones,mensajes}_2026.xml
├── camara/proyectos/{boletín}/ficha.xml
├── camara/proyectos/{boletín}/documento_ingreso.pdf
└── senado/tramitacion/{boletín}.xml
```

El almacén crudo y la base se usan mediante interfaces (`AlmacenCrudo`, `BaseDatos`) con una implementación local. Las de Cloudflare (R2 y D1) se agregan al migrar, sin cambiar la ingesta.

## Decisiones

| Tema | Estado |
|------|--------|
| Fuente de datos | ✅ Servicios web oficiales del Congreso (Senado, Cámara y BCN) |
| Legalidad | ✅ Uso libre declarado por el portal de datos abiertos del Congreso |
| Despliegue | ✅ Local primero; Cloudflare (free tier) como destino |
| Alcance de la fase 1 | ✅ Ventana de fechas configurable (`FECHA_DESDE`): último mes para desarrollar (reindexación rápida y barata) y periodo legislativo actual para evaluar y para la demo (un corpus chico infla las métricas de recuperación) |
| Lenguajes | 🟡 Propuesto: Python (ingesta) y TypeScript (Worker de consulta) |
| Base de datos y vector store | ✅ Todo en Cloudflare: D1 (SQLite + FTS5) para metadatos, tramitación y texto; Vectorize para la búsqueda semántica. Se descartó Postgres + pgvector externo para usar un solo proveedor; la interfaz del vector store permite migrar si el límite de dimensiones aprieta |
| Proveedor de embeddings | ✅ Workers AI (API REST): el corpus y las preguntas se vectorizan con el mismo modelo y backend, sin costo en la capa gratuita |
| Modelo de embeddings y chunking | ⏳ Se decide tras medir el corpus; candidatos: `bge-m3` y `qwen3-embedding-0.6b` (512 dims) |
| LLM | ⏳ Pendiente |
| Interfaz | ⏳ Pendiente |
| Licencia del código | ⏳ Pendiente |

## Flujo de trabajo

El desarrollo se realiza en la rama `development`. Los cambios se integran a `main` mediante Pull Request revisado y aprobado.
