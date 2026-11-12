# Fuente de datos: Datos Abiertos Legislativos

Relevamiento del 12-11-2026. Todos los servicios se probaron ese día: responden por HTTP GET, sin autenticación ni captcha.

Portal: [opendata.camara.cl](https://opendata.camara.cl/), una iniciativa conjunta de la Cámara de Diputadas y Diputados, el Senado y la Biblioteca del Congreso Nacional (BCN).

## Senado: `tramitacion.senado.cl/wspublico`

### Ficha y tramitación de un proyecto

```http
GET https://tramitacion.senado.cl/wspublico/tramitacion.php?boletin=8575-05
```

Devuelve XML (`application/xml`, ~64 KB para un proyecto largo):

```xml
<proyectos><proyecto>
  <descripcion>
    <boletin>8575-05</boletin>
    <titulo>Ley de Presupuestos del sector público para el año 2013.</titulo>
    <fecha_ingreso>01/10/2012</fecha_ingreso>
    <iniciativa>Mensaje</iniciativa>
    <camara_origen>C.Diputados</camara_origen>
    <urgencia_actual>Sin urgencia</urgencia_actual>
    <etapa>Tramitación terminada</etapa>
    <subetapa> /  </subetapa>
    <leynro>Ley N° 20.641</leynro>
    <diariooficial>22/12/2012</diariooficial>
    <estado>Publicado </estado>
    <refundidos></refundidos>
    <link_mensaje_mocion>http://www.senado.cl/appsenado/index.php?mo=tramitacion&amp;ac=getDocto&amp;iddocto=9000&amp;tipodoc=mensaje_mocion</link_mensaje_mocion>
  </descripcion>
  <autores>…</autores>
  <tramitacion>
    <tramite>
      <SESION>82/360</SESION><FECHA>02/10/2012</FECHA>
      <DESCRIPCIONTRAMITE>Cuenta de proyecto . Pasa a Comisión Especial Mixta de Presupuesto</DESCRIPCIONTRAMITE>
      <ETAPDESCRIPCION>Primer trámite constitucional</ETAPDESCRIPCION>
      <CAMARATRAMITE>C.Diputados</CAMARATRAMITE>
    </tramite>
    …
  </tramitacion>
  …
</proyecto></proyectos>
```

### Proyectos con movimiento desde una fecha (actualización incremental)

```http
GET https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha=01/11/2026
```

Formato de fecha `dd/mm/aaaa`. Devuelve el mismo XML para cada proyecto con movimiento desde esa fecha. Prueba: **154 proyectos** con movimiento entre el 01-11-2026 y el 12-11-2026 (1,7 MB), todos con `link_mensaje_mocion`.

> Nota: la página `invoca_tramitacion_fecha.html` describe este servicio. La ruta `tramitacion_fecha.php` responde 404; la correcta es `tramitacion.php?fecha=`.

### Otros servicios del Senado (enlazados desde el portal; formato por verificar)

| Servicio | Página |
|----------|--------|
| Votaciones por boletín | `https://tramitacion.senado.cl/wspublico/invoca_votacion.html` |
| Senadores vigentes | `https://tramitacion.senado.cl/wspublico/senadores_vigentes.php` |
| Sesiones de sala | `https://tramitacion.senado.cl/wspublico/invoca_sesion.html` |
| Diario de sesión | `https://tramitacion.senado.cl/wspublico/invoca_diario.html` |
| Comisiones vigentes | `https://tramitacion.senado.cl/wspublico/comisiones.php` |

## Cámara: `WSLegislativo.asmx`

Base: `https://opendata.camara.cl/camaradiputados/WServices/WSLegislativo.asmx`

Servicio ASMX que acepta HTTP GET con parámetros en la query. Namespace XML: `http://opendata.camara.cl/camaradiputados/v1`.

### Operaciones disponibles

`retornarDocumentoIngresoProyectoLey`, `retornarLegislaturaActual`, `retornarLegislaturas`, `retornarMaterias`, `retornarMensajesXAnno`, `retornarMocionesXAnno`, `retornarPeriodoLegislativoActual`, `retornarPeriodosLegislativos`, `retornarProyectoLey`, `retornarProyectosLeyxNumeroLey`, `retornarTramitesConstitucionales`, `retornarTramitesReglamentarios`, `retornarVotacionDetalle`, `retornarVotacionesXAnno`, `retornarVotacionesXProyectoLey`.

### Listado por año

```http
GET …/WSLegislativo.asmx/retornarMocionesXAnno?prmAnno=2026
GET …/WSLegislativo.asmx/retornarMensajesXAnno?prmAnno=2026
```

Prueba 2026: **773 mociones** (iniciativa parlamentaria, 372 KB) y **69 mensajes** (iniciativa del Ejecutivo, 34 KB). Cada elemento trae `Id`, `NumeroBoletin`, `Nombre`, `FechaIngreso`, `TipoIniciativa`, `CamaraOrigen` y `Admisible`.

### Ficha del proyecto

```http
GET …/WSLegislativo.asmx/retornarProyectoLey?prmNumeroBoletin=18115-27
```

```xml
<ProyectoLey xmlns="http://opendata.camara.cl/camaradiputados/v1">
  <Id>18778</Id>
  <NumeroBoletin>18115-27</NumeroBoletin>
  <Nombre>Regula la residencia, permanencia y el traslado hacia y desde el territorio especial del Archipiélago Juan Fernández…</Nombre>
  <FechaIngreso>2026-03-06T00:00:00</FechaIngreso>
  <TipoIniciativa Valor="1">Mensaje</TipoIniciativa>
  <CamaraOrigen Valor="2">Senado</CamaraOrigen>
  <MinisteriosPatrocinantes>
    <Ministerio><Id>225</Id><Nombre>Ministerio del Interior</Nombre></Ministerio>
    <Ministerio><Id>226</Id><Nombre>Ministerio de Seguridad Pública</Nombre></Ministerio>
  </MinisteriosPatrocinantes>
  <Votaciones />
  <Materias />
  <Admisible>true</Admisible>
</ProyectoLey>
```

### Texto del proyecto (documento de ingreso)

```http
GET …/WSLegislativo.asmx/retornarDocumentoIngresoProyectoLey?prmNumeroBoletin=18115-27
```

Devuelve el archivo **codificado en base64 dentro del XML**:

```xml
<Documento xmlns="http://opendata.camara.cl/camaradiputados/v1">
  <Nombre>18.115-27.pdf</Nombre>
  <ContentType>application/pdf</ContentType>
  <Archivo>JVBERi0x…</Archivo>
</Documento>
```

Prueba: XML de 481 KB → PDF de 22 páginas con **37.147 caracteres de texto extraíble** (texto nativo, sin OCR).

## BCN: LeyChile

[Web service de Legislación Abierta](https://www.bcn.cl/leychile/consulta/legislacion_abierta_web_service):

- Leyes más solicitadas.
- Metadatos de una norma y texto del encabezado.
- XML completo de la versión actualizada de una norma.

Ejemplo usado en otro proyecto: `https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=<id>` devuelve el XML completo de una norma.

## Estructura de los documentos

Los mensajes del Ejecutivo siguen un formato reconocible:

```
Boletín N° 18.115-27
Proyecto de ley, iniciado en Mensaje de Su Excelencia el Presidente de la República, que …
Santiago, 06 de marzo de 2026
MENSAJE Nº 320-373/
Honorable Senado:
  En uso de mis facultades constitucionales, …
I. ANTECEDENTES
  1. …
II. … (fundamentos, objetivos, contenido)
PROYECTO DE LEY
  Artículo 1.- …
```

**Ruido a limpiar en la extracción:**

- Notas al margen intercaladas con el texto (p. ej. `A S.E. EL PRESIDENTE DEL H. SENADO`).
- Números de página.
- Espacios partidos y saltos de línea dentro de párrafos.

Las mociones parlamentarias tienen un formato más variable: fundamentos y articulado, firmados por los autores.

## Volumen estimado

- ~840 proyectos ingresados por año (2026: 773 mociones + 69 mensajes a la fecha).
- Cada texto de ingreso tiene de 10 a 40 páginas, unos 20.000–40.000 caracteres.
- Un año completo equivale a varios millones de tokens: **excede el free tier de Vectorize** (~4.880 vectores de 1.024 dimensiones). Ver opciones en `despliegue.md`.

## Buenas prácticas de descarga

- Servicios antiguos (ASMX/PHP): una solicitud a la vez, con pausas de 1 a 2 segundos.
- Caché local: no volver a descargar un boletín ya obtenido, salvo para actualizar su tramitación.
- Guardar siempre el XML crudo y el PDF decodificado como fuente de verdad.
- User-Agent genérico del proyecto.
