# Revisión del código de ingesta

Revisión archivo por archivo del código de ingesta (PR #4), en orden de creación, antes de pasar a la extracción de texto de los PDF. Si un archivo necesita cambios, se sigue el flujo de `CLAUDE.md`: planificación → aprobación → codificación.

Estados: ⏳ pendiente · ✅ validado · 🔧 con cambios

| # | Archivo(s) | Por qué es necesario | Líneas | Estado |
|---|---|---|---:|---|
| 1 | `pyproject.toml` | Declara el paquete y la versión de Python (3.12 o superior). Deja el proyecto listo para `uv` cuando se agreguen dependencias | 8 | ⏳ |
| 2 | `.env.example` | Plantilla del `.env`: rutas, endpoints y parámetros quedan fuera del código | 17 | ⏳ |
| 3 | `proyectos_ley/config.py` | Lee y valida esas variables (y el `.env`) en un único objeto `Config` | 74 | ⏳ |
| 4 | `proyectos_ley/almacenamiento/crudo.py` | Interfaz `AlmacenCrudo` con implementación local (`data/raw`); después R2. Los archivos crudos son la fuente de verdad | 63 | ⏳ |
| 5 | `proyectos_ley/fuentes/http.py` | Descarga responsable: una solicitud a la vez, pausas de 1 a 2 s y reintentos ante errores temporales | 78 | ⏳ |
| 6 | `proyectos_ley/fuentes/xml.py` | Funciones comunes para leer XML: texto limpio y fechas (ISO y dd/mm/aaaa) | 27 | ⏳ |
| 7 | `proyectos_ley/fuentes/camara.py` | Lee los listados, la ficha (autores y ministerios) y el documento de ingreso en base64 de la Cámara | 159 | ⏳ |
| 8 | `proyectos_ley/fuentes/senado.py` | Lee la tramitación del Senado (etapa, estado y trámites). Maneja el boletín sin sufijo y la respuesta HTML de "no existe" | 92 | ⏳ |
| 9 | `proyectos_ley/db/esquema.sql` | Tablas de la base relacional, en SQLite compatible con D1. De aquí salen las cifras y los estados, no del LLM | 67 | ⏳ |
| 10 | `proyectos_ley/db/base.py` | Interfaz `BaseDatos` (lotes atómicos, como D1) con implementación SQLite | 52 | ⏳ |
| 11 | `proyectos_ley/db/repositorio.py` | Arma los INSERT de cada proyecto (ficha, tramitación y documentos). Repetir la carga no duplica datos | 113 | ⏳ |
| 12 | `proyectos_ley/ingesta/claves.py` | Define en un solo lugar cómo se organizan los archivos en `data/raw` (claves compatibles con R2) | 37 | ⏳ |
| 13 | `proyectos_ley/ingesta/descargar.py` | Comando 1: servicios web → `data/raw`, con caché y filtro por `FECHA_DESDE`. Es el único que usa la red | 182 | ⏳ |
| 14 | `proyectos_ley/ingesta/cargar.py` | Comando 2: `data/raw` → SQLite, sin red. Permite borrar y regenerar la base | 104 | ⏳ |
| 15 | `tests/fixtures/*` | Respuestas reales (recortadas) de la Cámara y el Senado para probar sin red | ~110 | ⏳ |
| 16 | `tests/test_fuentes.py`, `tests/test_ingesta.py` | 15 tests: parsers, caché, actualización de la tramitación y carga sin duplicados | 219 | ⏳ |

Los `__init__.py` solo tienen un docstring. En el mismo PR también cambió la documentación (`README.md`, `docs/fuente-de-datos.md` y `CLAUDE.md`), que ya se conversó.

## Notas de la revisión

<!-- Observaciones y decisiones por archivo, a medida que se revisen. -->
