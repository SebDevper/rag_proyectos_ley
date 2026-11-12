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
| 1 | Proyectos ingresados en el periodo legislativo actual (desde el 11-03-2026): metadatos, tramitación y texto de ingreso | 🚧 Por iniciar |
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

## Decisiones

| Tema | Estado |
|------|--------|
| Fuente de datos | ✅ Servicios web oficiales del Congreso (Senado, Cámara y BCN) |
| Legalidad | ✅ Uso libre declarado por el portal de datos abiertos del Congreso |
| Despliegue | ✅ Local primero; Cloudflare (free tier) como destino |
| Alcance de la fase 1 | 🟡 Propuesto: periodo legislativo actual |
| Lenguajes | 🟡 Propuesto: Python (ingesta) y TypeScript (Worker de consulta) |
| Modelo de embeddings y chunking | ⏳ Se decide tras medir el corpus |
| LLM | ⏳ Pendiente |
| Interfaz | ⏳ Pendiente |
| Licencia del código | ⏳ Pendiente |

## Flujo de trabajo

El desarrollo se realiza en la rama `development`. Los cambios se integran a `main` mediante Pull Request revisado y aprobado.
