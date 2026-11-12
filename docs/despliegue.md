# Despliegue

## Estrategia

El desarrollo se hace **primero en local**, paso a paso. Todo lo que se construya debe poder **migrarse a Cloudflare sin reescribir la lógica**: cada componente de infraestructura tiene un equivalente local y uno en la nube detrás de la misma interfaz.

## Opción 1 (preferida): Cloudflare, capa gratuita

Límites revisados el 12-11-2026 con la [documentación oficial](https://developers.cloudflare.com/). Pueden cambiar.

| Rol | Cloudflare | Free tier | Equivalente local |
|-----|------------|-----------|-------------------|
| API de consulta | **Workers** | 100.000 req/día; 10 ms de CPU/invocación (sin contar espera de I/O) | Servidor HTTP local |
| Almacenamiento crudo (XML, PDF) | **R2** | 10 GB | Directorio `data/raw` |
| Metadatos, tramitación, votaciones, texto y búsqueda léxica | **D1** (SQLite + FTS5) | 5 GB; 5M filas leídas/día | SQLite con FTS5 |
| Búsqueda semántica | **Vectorize** | 5M dimensiones almacenadas; 30M consultadas/mes; máx. 1.536 dims | Vector store local |
| Embeddings, reranker, LLM | **Workers AI** | 10.000 neurons/día (bolsa compartida) | Modelos locales o API de Workers AI |
| Actualización diaria | **Cron Triggers** o GitHub Actions | — | Script programado |
| Frontend | **Workers Static Assets** | Ilimitado | Servidor local |
| Protección del endpoint público | **Turnstile**, **AI Gateway** | Gratis | — |

La **ingesta** (descarga, decodificación de PDF, extracción y embeddings) corre fuera de Workers: en Python, local o en GitHub Actions. Procesar PDFs excede los 10 ms de CPU del plan gratuito.

### Presupuesto para este corpus

**Vectorize, 5M de dimensiones almacenadas: el límite crítico.**

| Embedding | Dimensiones | Vectores máximos |
|-----------|------------:|-----------------:|
| `bge-m3` | 1.024 | ~4.880 |
| `qwen3-embedding-0.6b` (reducido por MRL) | 512 | ~9.760 |

Un año de proyectos (~840 textos de 20.000–40.000 caracteres) genera decenas de miles de chunks. Opciones, a decidir tras medir:

1. **Acotar el corpus:** periodo legislativo actual, solo mensajes del Ejecutivo o un tema.
2. **Chunks más grandes por sección** (antecedentes, fundamentos, articulado) y vectores de menor dimensión.
3. **Indexar resúmenes por proyecto** en Vectorize y usar FTS5 (D1) para el texto completo.
4. **Plan Workers Paid** (US$5/mes), que sube el límite a 10M de dimensiones almacenadas incluidas.

**Workers AI, 10.000 neurons/día:**

- Embeddings con `bge-m3`: ~1.075 neurons por millón de tokens.
- Respuesta con `gpt-oss-120b`: ~160 neurons → **~60 consultas/día**.
- Respuesta con `qwen3-30b-a3b`: ~35 neurons → **~290 consultas/día**.
- Al ser público, proteger con Turnstile, rate limiting y caché.

## Principios de portabilidad

1. **Interfaces de almacenamiento:** el almacenamiento crudo, la base relacional y el vector store se acceden mediante interfaces con implementación local y para Cloudflare (R2, D1, Vectorize).
2. **SQL compatible con D1:** SQLite estándar con FTS5.
3. **Restricciones de Vectorize desde el inicio:** máx. 1.536 dimensiones, 10 KiB de metadatos por vector, hasta 10 índices de metadatos y `topK` ≤ 50 con metadatos.
4. **Mismos modelos en local y en la nube:** los disponibles en Workers AI.
5. **Configuración por variables de entorno:** sin rutas, claves ni endpoints en el código.
6. **Datos crudos como fuente de verdad:** cualquier índice debe poder regenerarse desde los XML y PDF guardados.

## Fuentes

- [Workers – Pricing](https://developers.cloudflare.com/workers/platform/pricing/) · [Limits](https://developers.cloudflare.com/workers/platform/limits)
- [Vectorize – Pricing](https://developers.cloudflare.com/vectorize/platform/pricing/) · [Limits](https://developers.cloudflare.com/vectorize/platform/limits/)
- [Workers AI – Pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/)
