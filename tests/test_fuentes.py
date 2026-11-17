import base64
import unittest
from datetime import date
from pathlib import Path

from proyectos_ley.fuentes import camara, senado

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(nombre: str) -> bytes:
    return (FIXTURES / nombre).read_bytes()


def documento_xml(contenido: bytes, content_type: str = "application/pdf") -> bytes:
    archivo = base64.b64encode(contenido).decode()
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<Documento xmlns="http://opendata.camara.cl/camaradiputados/v1">'
        f"<Nombre>18.115-27.pdf</Nombre><ContentType>{content_type}</ContentType>"
        f"<Archivo>{archivo}</Archivo></Documento>"
    ).encode()


class TestCamara(unittest.TestCase):
    def test_listado(self):
        proyectos = camara.parsear_listado(fixture("camara_listado_mensajes.xml"))
        self.assertEqual([p.boletin for p in proyectos], ["18115-27", "18730-29"])
        reciente = proyectos[1]
        self.assertEqual(reciente.camara_id, 19411)
        self.assertEqual(reciente.fecha_ingreso, date(2026, 10, 7))
        self.assertEqual(reciente.tipo_iniciativa, "Mensaje")
        self.assertEqual(reciente.camara_origen, "Cámara de Diputados")
        self.assertTrue(reciente.admisible)

    def test_ficha_mocion_con_autores(self):
        ficha = camara.parsear_ficha(fixture("camara_ficha_mocion.xml"))
        self.assertEqual(ficha.proyecto.boletin, "18882-25")
        self.assertEqual(ficha.proyecto.tipo_iniciativa, "Moción")
        self.assertEqual(len(ficha.autores), 3)
        self.assertEqual(ficha.autores[0], camara.Autor(1117, "Iván Moreira Barros", "Senado"))
        self.assertEqual(ficha.ministerios, [])

    def test_ficha_mensaje_con_ministerios(self):
        ficha = camara.parsear_ficha(fixture("camara_ficha_mensaje.xml"))
        self.assertEqual(ficha.autores, [])
        self.assertEqual([m.ministerio_id for m in ficha.ministerios], [225, 226])

    def test_documento_se_decodifica(self):
        documento = camara.parsear_documento(documento_xml(b"%PDF-1.4 contenido"))
        self.assertEqual(documento.contenido, b"%PDF-1.4 contenido")
        self.assertEqual(documento.extension, "pdf")

    def test_documento_vacio(self):
        self.assertIsNone(camara.parsear_documento(documento_xml(b"")))

    def test_respuesta_inesperada(self):
        with self.assertRaises(camara.RespuestaInvalida):
            camara.parsear_ficha(b"<html>error</html>")


class TestSenado(unittest.TestCase):
    def test_numero_boletin_sin_sufijo(self):
        self.assertEqual(senado.numero_boletin("18882-25"), "18882")

    def test_tramitacion(self):
        t = senado.parsear_tramitacion(fixture("senado_tramitacion.xml"))
        self.assertEqual(t.boletin, "18882-25")
        self.assertEqual(t.etapa, "Primer trámite constitucional (Senado)")
        self.assertEqual(t.estado, "En tramitación")  # sin el espacio final del XML
        self.assertIsNone(t.ley_numero)
        self.assertEqual(len(t.tramites), 2)
        ingreso, cuenta = t.tramites
        self.assertIsNone(ingreso.sesion)  # el Senado usa "/" como vacío
        self.assertEqual(ingreso.fecha, date(2026, 11, 10))
        self.assertEqual(cuenta.sesion, "79/374")
        self.assertEqual(cuenta.orden, 2)

    def test_boletin_inexistente(self):
        self.assertIsNone(senado.parsear_tramitacion(fixture("senado_no_existe.html")))


if __name__ == "__main__":
    unittest.main()
