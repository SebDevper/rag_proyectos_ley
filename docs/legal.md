# Análisis legal

Revisión del 12-11-2026.

> Este documento no constituye asesoría legal. Es un análisis orientativo para tomar decisiones de diseño.

## Conclusión

**Riesgo bajo.** El Congreso Nacional publica estos datos en un portal de datos abiertos que declara expresamente su uso libre, incluso para crear aplicaciones propias.

## Declaración del portal de Datos Abiertos Legislativos

[opendata.camara.cl](https://opendata.camara.cl/), iniciativa conjunta de la Cámara de Diputadas y Diputados, el Senado y la Biblioteca del Congreso Nacional:

> *"En esta sección se puede acceder a los antecedentes que se producen con ocasión de la tramitación de un proyecto de ley, información de los parlamentarios y leyes ya publicadas, en un formato que permita su utilización **libre de trabas o restricciones como derechos de autor, licencias u otros mecanismos de control**. Estos datos pueden ser utilizados libremente por los ciudadanos, para generar sus propias aplicaciones, como producto del cruce de la información."*

La declaración cubre la tramitación, la información de parlamentarios y las leyes publicadas, para las tres instituciones.

## Contexto normativo

- **Constitución, art. 8:** son públicos los actos y resoluciones de los órganos del Estado, así como sus fundamentos.
- **Ley 17.336 de Propiedad Intelectual:**
  - El **art. 88** asigna al Estado el derecho de autor de las obras de sus funcionarios. La declaración del portal renuncia expresamente a esas restricciones para los datos que publica.
  - El **art. 71 D** permite usar libremente, con fines de información, *"las conferencias, discursos políticos, alegatos judiciales y otras obras del mismo carácter que hayan sido pronunciadas en público"*. Es relevante si se incorporan debates o el diario de sesiones.
- **Ley 21.459 de Delitos Informáticos:** el acceso ilícito exige *"superar barreras técnicas"*. Los servicios son públicos, sin autenticación ni captcha, así que no aplica.

## Comparación con el proyecto anterior (rag_sii)

| Aspecto | SII (pausado) | Congreso (este proyecto) |
|---------|---------------|--------------------------|
| Permiso de uso | Términos que exigen autorización escrita para fines públicos | Declaración expresa de uso libre, sin derechos de autor ni licencias |
| Acceso | API no documentada | Servicios web oficiales publicados para reutilización |
| Texto completo | PDF por API interna | PDF entregado por el servicio oficial |

## Datos personales

- Los parlamentarios y autoridades aparecen en ejercicio de su función pública.
- Algunos proyectos nombran a personas particulares: por ejemplo, los que *"rehabilitan la nacionalidad chilena a doña…"* o los que conceden pensiones de gracia. Son registros públicos, pero **no se destacarán ni se usarán como ejemplos** en el producto.
- La Ley 21.719 entraría en vigencia el 01-12-2026, con un proyecto de postergación en trámite. El tratamiento de información de fuentes públicas oficiales con fines informativos es de bajo riesgo, pero hay que revisarlo si el producto crece.

## Compromisos del proyecto

1. **Citar siempre la fuente:** boletín, documento y enlace al sitio oficial.
2. **Aviso visible:** herramienta informativa, no oficial y sin afiliación con el Congreso, la Cámara, el Senado ni la BCN. No usar sus logos.
3. **No alterar el sentido de los textos:** las respuestas generadas se distinguen de los textos oficiales citados.
4. **Descarga responsable:** pausas entre solicitudes, caché local y sin concurrencia.
5. **No destacar a personas particulares** mencionadas en los proyectos.

## Fuentes

- [Datos Abiertos Legislativos del Congreso Nacional](https://opendata.camara.cl/)
- [Ley 17.336 de Propiedad Intelectual](https://www.bcn.cl/leychile/navegar?idNorma=28933)
- [Ley 21.459 de Delitos Informáticos](https://www.bcn.cl/leychile/navegar?i=1177743)
