import tempfile
import unittest
from datetime import date
from pathlib import Path

from proyectos_ley.almacenamiento.crudo import AlmacenCrudoLocal
from proyectos_ley.config import Config
from proyectos_ley.db.base import BaseDatosSQLite
from proyectos_ley.ingesta.cargar import cargar
from proyectos_ley.ingesta.descargar import descargar
from tests.test_fuentes import documento_xml, fixture

CAMARA = "https://camara.test/ws"
SENADO = "https://senado.test/tramitacion.php"

LISTADO_VACIO = (
    b'<?xml version="1.0" encoding="utf-8"?>'
    b'<ProyectosLeyColeccion xmlns="http://opendata.camara.cl/camaradiputados/v1" />'
)


def config(raiz: Path) -> Config:
    return Config(
        dir_crudo=raiz / "raw",
        ruta_db=raiz / "db.sqlite",
        camara_ws_url=CAMARA,
        senado_ws_url=SENADO,
        user_agent="test",
        pausa_min=1,
        pausa_max=2,
        fecha_desde=None,
    )


class ClienteFalso:
    """Responde con fixtures según la operación y registra cada solicitud."""

    def __init__(self, senado_existe: bool = True):
        self.senado_existe = senado_existe
        self.solicitudes: list[tuple[str, dict]] = []

    def get(self, url, params=None):
        self.solicitudes.append((url, params))
        if url == f"{CAMARA}/retornarMensajesXAnno":
            return fixture("camara_listado_mensajes.xml")
        if url == f"{CAMARA}/retornarMocionesXAnno":
            return LISTADO_VACIO
        if url == f"{CAMARA}/retornarProyectoLey":
            return fixture("camara_ficha_mensaje.xml").replace(b"18115-27", params["prmNumeroBoletin"].encode())
        if url == f"{CAMARA}/retornarDocumentoIngresoProyectoLey":
            return documento_xml(b"%PDF-1.4 texto")
        if url == SENADO:
            if not self.senado_existe:
                return fixture("senado_no_existe.html")
            return fixture("senado_tramitacion.xml").replace(b"18882-25", f"{params['boletin']}-29".encode())
        raise AssertionError(f"URL inesperada: {url}")

    def operaciones(self):
        return [url.rsplit("/", 1)[-1] for url, _ in self.solicitudes]


class TestDescarga(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = config(Path(self.tmp.name))
        self.almacen = AlmacenCrudoLocal(self.config.dir_crudo)

    def tearDown(self):
        self.tmp.cleanup()

    def test_filtra_por_fecha_y_guarda_crudos(self):
        cliente = ClienteFalso()
        resumen = descargar(cliente, self.almacen, self.config, date(2026, 10, 1), hasta=date(2026, 11, 16))
        self.assertEqual(resumen.proyectos, 1)  # el mensaje de marzo queda fuera
        self.assertEqual(resumen.errores, {})
        self.assertTrue(self.almacen.existe("camara/proyectos/18730-29/ficha.xml"))
        self.assertEqual(self.almacen.leer("camara/proyectos/18730-29/documento_ingreso.pdf"), b"%PDF-1.4 texto")
        self.assertTrue(self.almacen.existe("senado/tramitacion/18730-29.xml"))
        # Al Senado se le pide el número sin sufijo
        self.assertIn((SENADO, {"boletin": "18730"}), cliente.solicitudes)

    def test_segunda_corrida_usa_cache(self):
        descargar(ClienteFalso(), self.almacen, self.config, date(2026, 10, 1), hasta=date(2026, 11, 16))
        cliente = ClienteFalso()
        resumen = descargar(cliente, self.almacen, self.config, date(2026, 10, 1), hasta=date(2026, 11, 16))
        self.assertEqual(resumen.en_cache, 1)
        self.assertEqual(cliente.operaciones(), ["retornarMocionesXAnno", "retornarMensajesXAnno"])

    def test_actualizar_tramitacion_solo_pide_al_senado(self):
        descargar(ClienteFalso(), self.almacen, self.config, date(2026, 10, 1), hasta=date(2026, 11, 16))
        cliente = ClienteFalso()
        descargar(
            cliente, self.almacen, self.config, date(2026, 10, 1), hasta=date(2026, 11, 16), actualizar_tramitacion=True
        )
        self.assertEqual(cliente.operaciones()[2:], ["tramitacion.php"])

    def test_boletin_aun_no_esta_en_el_senado(self):
        resumen = descargar(
            ClienteFalso(senado_existe=False), self.almacen, self.config, date(2026, 10, 1), hasta=date(2026, 11, 16)
        )
        self.assertEqual(resumen.sin_tramitacion, ["18730-29"])
        self.assertFalse(self.almacen.existe("senado/tramitacion/18730-29.xml"))


class TestCarga(unittest.TestCase):
    def test_carga_desde_crudos_es_idempotente(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = config(Path(tmp))
            almacen = AlmacenCrudoLocal(cfg.dir_crudo)
            descargar(ClienteFalso(), almacen, cfg, date(2026, 10, 1), hasta=date(2026, 11, 16))
            db = BaseDatosSQLite(":memory:")
            cargar(almacen, db)
            resumen = cargar(almacen, db)  # segunda carga: mismos resultados, sin duplicados

            self.assertEqual(resumen.cargados, 1)
            proyecto = db.consultar("SELECT * FROM proyectos")[0]
            self.assertEqual(proyecto["boletin"], "18730-29")
            self.assertEqual(proyecto["tipo_iniciativa"], "Mensaje")
            self.assertEqual(proyecto["estado"], "En tramitación")
            self.assertEqual(db.consultar("SELECT count(*) AS n FROM tramites")[0]["n"], 2)
            self.assertEqual(db.consultar("SELECT count(*) AS n FROM ministerios_patrocinantes")[0]["n"], 2)
            documento = db.consultar("SELECT * FROM documentos")[0]
            self.assertEqual(documento["clave_crudo"], "camara/proyectos/18730-29/documento_ingreso.pdf")
            self.assertEqual(documento["bytes"], len(b"%PDF-1.4 texto"))


class TestAlmacen(unittest.TestCase):
    def test_rechaza_claves_fuera_del_almacen(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                AlmacenCrudoLocal(Path(tmp)).guardar("../fuera.txt", b"x")


if __name__ == "__main__":
    unittest.main()
