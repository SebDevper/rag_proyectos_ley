# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Proyecto

Asistente (RAG + datos estructurados) sobre los proyectos de ley del Congreso Nacional de Chile. Es un producto público de portafolio orientado a **reclutadores**: la calidad del código, la documentación y la demo importan, y los ejemplos deben ser comprensibles para alguien no técnico.

- **Objetivo del usuario:** aprender a construir sistemas RAG y mostrarlos en su portafolio. Explicar las decisiones técnicas cuando se tomen.
- **Idioma:** conversación, documentación y mensajes de commit en español.
- **Decisiones abiertas** (alcance de la fase 1, stack, embeddings, LLM, interfaz, licencia del código): se definen junto al usuario. Proponer con recomendación; no imponer. El estado está en la tabla "Decisiones" del `README.md`.
- **Antecedente:** reemplaza al proyecto `~/workspace/rag_sii`, pausado por riesgos legales. Este proyecto reutiliza su arquitectura y principios.

## Documentación

- `docs/fuente-de-datos.md`: servicios web del Senado, la Cámara y la BCN, con ejemplos probados y volúmenes.
- `docs/legal.md`: permiso de uso del portal de datos abiertos y compromisos del proyecto.
- `docs/despliegue.md`: Cloudflare como destino, presupuesto de límites y principios de portabilidad.

## Forma de trabajo: planificación → aprobación → codificación

Todo cambio de código pasa por tres etapas. **Cada etapa la inicia el usuario**: no avanzar por cuenta propia de una a la siguiente.

1. **Planificación:** presentar un plan antes de escribir código: qué se hará y por qué, archivos que se crean o modifican, tamaño aproximado del cambio y decisiones técnicas con su justificación. En esta etapa no se escribe código.
2. **Aprobación:** esperar la aprobación explícita del usuario. Aprobar un plan no autoriza otro plan ni cambios fuera de su alcance.
3. **Codificación:** cada paso del plan aprobado lo implementa un agente distinto (subagente), ciñéndose al plan. Si aparece algo que obliga a desviarse, detenerse y consultarlo.

- **Sin grandes cantidades de código sin comentarlo antes.** Dividir el trabajo en pasos pequeños que el usuario pueda revisar y validar.
- Los ajustes menores de documentación pedidos explícitamente por el usuario pueden hacerse directamente.

## Flujo de trabajo con Git

1. Trabajar **solo en la rama `development`**. Nunca commitear ni hacer push directo a `main`.
2. Antes de empezar, sincronizar: `git fetch` y verificar que `development` esté al día con `origin/development` y que incluya `origin/main` (si `main` tiene merges que `development` no tiene, integrarlos con `git merge origin/main`).
3. **Antes de cada push, revisar el estado del PR:** `gh pr list --state all`. El usuario puede mergear o cerrar un PR en cualquier momento, incluso a mitad de una sesión, así que no basta con haberlo revisado al inicio.
   - **PR abierto** desde `development`: el push lo actualiza; ajustar título y descripción si cambia el alcance.
   - **PR mergeado o cerrado:** no editarlo ni darlo por actualizado. Después del push, abrir un PR nuevo `development → main`.
   - Tras crear o actualizar un PR, confirmar con `git log origin/main..origin/development` qué commits incluye: todo commit que no esté en `main` debe quedar cubierto por un PR abierto.
4. Hacer commit de los cambios y push a `origin/development`.
5. El usuario revisa y aprueba el PR. **Nunca mergear PRs por cuenta propia.**
6. Si `gh pr edit` falla con un error de "Projects (classic)", editar el PR con la API REST: `gh api -X PATCH repos/{owner}/{repo}/pulls/{n} -f title=... -f body=...`.

## Desarrollo: local primero, portable a Cloudflare

Todo se construye y prueba en local, pero debe poder migrarse a la capa gratuita de Cloudflare sin reescribir la lógica (detalles en `docs/despliegue.md`):

- El almacenamiento crudo, la base relacional y el vector store se acceden mediante interfaces con una implementación local y otra para Cloudflare (R2, D1, Vectorize).
- SQL compatible con D1: SQLite estándar con FTS5.
- Respetar los límites de Vectorize: máximo 1.536 dimensiones, 5M de dimensiones almacenadas en el free tier, 10 KiB de metadatos por vector y `topK` ≤ 50 con metadatos.
- Usar los mismos modelos disponibles en Workers AI.
- Configuración por variables de entorno; sin rutas, claves ni endpoints en el código.
- Los XML y PDF crudos son la fuente de verdad; cualquier índice debe poder regenerarse desde ellos.

## Reglas de datos

- **Nunca descargar ni llamar a servicios o APIs externas sin consentimiento explícito del usuario:** servicios del Congreso, Workers AI, Cloudflare u otros, incluidas las pruebas exploratorias con `curl` y los scripts de ingesta. Antes de cada ejecución que use la red, explicar qué se llamará, cuántas solicitudes aproximadas y para qué, y esperar la aprobación. El consentimiento vale para esa ejecución, no para las siguientes. Buscar y leer documentación pública en la web no requiere consentimiento.
- **Descarga responsable:** una solicitud a la vez, pausas de 1 a 2 segundos, caché local y sin volver a descargar boletines ya obtenidos (salvo para actualizar su tramitación).
- **El corpus no va al repositorio:** `data/` está en `.gitignore`.
- **Citas obligatorias:** toda respuesta cita boletín, documento o trámite con enlace a la fuente oficial. Si no hay respaldo, el sistema lo dice.
- **Cifras y estados desde los datos:** fechas, etapas y votaciones salen de consultas a los datos estructurados, nunca del texto generado por el LLM.
- **No destacar personas particulares** mencionadas en proyectos (p. ej. nacionalidad por gracia o pensiones de gracia).
- **Aviso en el producto:** herramienta informativa, no oficial, sin afiliación con el Congreso; sin logos institucionales.
