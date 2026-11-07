"""Tests de la biblioteca. No necesitan una base de datos real."""
import time
from datetime import date

import pytest

import app as modulo_app
from app import validar

# ---------- Tests de la función validar() ----------

def test_validar_datos_correctos():
    errores, anio = validar("El Quijote", "Cervantes", "1605")
    assert errores == []
    assert anio == 1605


def test_validar_anio_vacio_es_valido():
    # El año es opcional: si no se escribe, no hay error y queda como None
    errores, anio = validar("El Quijote", "Cervantes", "")
    assert errores == []
    assert anio is None


def test_validar_titulo_y_autor_obligatorios():
    errores, _ = validar("", "", "")
    assert "El título es obligatorio." in errores
    assert "El autor es obligatorio." in errores


@pytest.mark.parametrize("anio_texto", ["999", str(date.today().year + 1)])
def test_validar_anio_fuera_de_rango(anio_texto):
    # Se prueban los dos límites: antes del año 1000 y después del año actual
    errores, _ = validar("Título", "Autor", anio_texto)
    assert errores == [f"El año debe estar entre 1000 y {date.today().year}."]


def test_validar_anio_no_numerico():
    errores, _ = validar("Título", "Autor", "mil")
    assert errores == ["El año debe ser un número entero."]


# ---------- Tests de las rutas web ----------

@pytest.fixture
def cliente():
    """Cliente de pruebas de Flask: hace peticiones sin arrancar un servidor."""
    modulo_app.app.config["TESTING"] = True
    return modulo_app.app.test_client()


def test_formulario_nuevo(cliente):
    # GET /nuevo solo pinta el formulario, no se conecta a la base de datos
    respuesta = cliente.get("/nuevo")
    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)
    assert "<form" in html
    assert 'name="titulo"' in html
    assert 'name="autor"' in html


def test_lista_sin_base_de_datos_devuelve_503(cliente, monkeypatch):
    # Apuntamos a un puerto cerrado (el 1): la conexión se rechaza al instante.
    # monkeypatch cambia la variable solo durante este test.
    monkeypatch.setattr(modulo_app, "DATABASE_URL", "postgresql://u:p@127.0.0.1:1/x")
    inicio = time.monotonic()
    respuesta = cliente.get("/")
    duracion = time.monotonic() - inicio
    # La app debe mostrar la página de error amable (503), no una traza (500)
    assert respuesta.status_code == 503
    # Y debe hacerlo rápido: muy por debajo de los 30 s en que gunicorn corta la petición
    assert duracion < 10


# ---------- Tests de la ruta /health ----------

def test_health_sin_base_de_datos_devuelve_503(cliente, monkeypatch, caplog):
    # Mismo truco que en el test de la lista: un puerto cerrado rechaza la conexión al instante
    monkeypatch.setattr(modulo_app, "DATABASE_URL", "postgresql://u:p@127.0.0.1:1/x")
    inicio = time.monotonic()
    respuesta = cliente.get("/health")
    duracion = time.monotonic() - inicio
    assert respuesta.status_code == 503
    # Debe responder JSON (no la página error.html) y sin detalles de la conexión
    assert respuesta.get_json() == {"status": "error", "db": "unreachable"}
    assert duracion < 10
    # caplog recoge lo que se escribe en el log durante el test: el error real debe quedar registrado
    assert "Healthcheck fallido" in caplog.text


def test_health_sin_database_url_devuelve_503(cliente, monkeypatch, caplog):
    # Sin DATABASE_URL, conectar() lanza RuntimeError: /health también debe responder JSON
    monkeypatch.setattr(modulo_app, "DATABASE_URL", None)
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 503
    assert respuesta.get_json() == {"status": "error", "db": "unreachable"}
    assert "Healthcheck fallido" in caplog.text


class ConexionFalsa:
    """Imita lo mínimo de una conexión de psycopg que usa /health: el bloque with y execute()."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, consulta):
        pass


def test_health_con_base_de_datos_devuelve_200(cliente, monkeypatch):
    # Un "doble de prueba" es un objeto falso que sustituye a uno real durante un test.
    # Aquí solo queremos probar la lógica de /health, no PostgreSQL, así que basta con fingir que conecta.
    monkeypatch.setattr(modulo_app, "conectar", lambda: ConexionFalsa())
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"status": "ok", "db": "ok"}
