"""Batería de ia_tests_propuesta.py, corregida (Parte D).

    python -m pytest tests/test_ia_corregido.py -v

Correcciones respecto a la propuesta de la IA (detalle en DICTAMEN_IA.md):

1. Aserciones que no podían fallar (`status_code in (200, 201, 422)`, `< 500`,
   `"puntaje" in ... or "error" in ...`) pasan a exigir UN resultado concreto.
2. El «aislamiento» sustituía una función get_db local que la aplicación nunca
   usa, así que las pruebas escribían en app.db. Ahora se sustituye
   database.get_db por una sesión sobre una base SQLite temporal y vacía por test,
   y cada prueba comprueba el efecto (lo creado se puede volver a leer, la
   predicción queda registrada), no solo el código de estado.
3. Los datos aleatorios sin semilla (random.choice, random.uniform) hacían que el
   resultado dependiera de la corrida. Ahora los casos son fijos y explícitos con
   pytest.mark.parametrize, incluidos los extremos.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

# Antes de importar la app, para que ni siquiera al arrancar apunte a app.db.
os.environ.setdefault("DATABASE_URL", f"sqlite:///{Path(tempfile.gettempdir()) / 'polizas_ia.db'}")

import modelos  # noqa: E402,F401  (registra las tablas en Base.metadata)
from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture
def cliente(tmp_path):
    """Cliente sobre una base temporal NUEVA y vacía para cada test."""
    engine = create_engine(f"sqlite:///{tmp_path / 'ia.db'}",
                           connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _claves_foraneas(conexion, _registro):
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine, autoflush=False)

    def _get_db_prueba():
        db = Sesion()
        try:
            yield db
        finally:
            db.close()

    # Se sustituye la dependencia que la aplicación USA de verdad: database.get_db.
    app.dependency_overrides[get_db] = _get_db_prueba
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def _poliza(numero="POL-IA-000001", **extra) -> dict:
    base = {
        "numero": numero,
        "asegurado": "Prueba Automática",
        "tipo": "auto",
        "prima": 1_250_000,
        "fecha_inicio": "2026-01-01",
        "fecha_fin": "2026-12-31",
    }
    base.update(extra)
    return base


# --- Defecto 1: aserciones que no podían fallar --------------------------------

def test_crear_poliza_responde_201_y_se_puede_leer(cliente):
    r = cliente.post("/polizas", json=_poliza())
    assert r.status_code == 201
    creada = r.json()
    assert creada["numero"] == "POL-IA-000001"
    assert "token_firma" not in creada
    # Se guardó de verdad: se puede volver a leer.
    leida = cliente.get(f"/polizas/{creada['id']}")
    assert leida.status_code == 200
    assert leida.json()["numero"] == "POL-IA-000001"


def test_consultar_poliza_inexistente_da_404(cliente):
    assert cliente.get("/polizas/999999").status_code == 404


def test_listar_polizas_devuelve_las_creadas(cliente):
    cliente.post("/polizas", json=_poliza("POL-IA-000001"))
    cliente.post("/polizas", json=_poliza("POL-IA-000002"))
    r = cliente.get("/polizas")
    assert r.status_code == 200
    assert [p["numero"] for p in r.json()] == ["POL-IA-000001", "POL-IA-000002"]


def test_numero_duplicado_da_409(cliente):
    assert cliente.post("/polizas", json=_poliza()).status_code == 201
    assert cliente.post("/polizas", json=_poliza()).status_code == 409


def test_fechas_invertidas_dan_422(cliente):
    r = cliente.post("/polizas", json=_poliza(fecha_inicio="2026-12-31", fecha_fin="2026-01-01"))
    assert r.status_code == 422


@pytest.mark.parametrize("prima", [0, -1])
def test_prima_no_positiva_da_422(cliente, prima):
    assert cliente.post("/polizas", json=_poliza(prima=prima)).status_code == 422


# --- Defecto 3: datos aleatorios sin semilla -> casos fijos y explícitos -------

@pytest.mark.parametrize("tipo", ["auto", "hogar", "vida"])
@pytest.mark.parametrize("prima", [1, 2_500_000, 4_999_999.99])
def test_primas_y_tipos_validos_son_aceptados(cliente, tipo, prima):
    r = cliente.post("/polizas", json=_poliza(tipo=tipo, prima=prima))
    assert r.status_code == 201
    assert r.json()["tipo"] == tipo
    assert r.json()["prima"] == prima


def test_resumen_cuenta_y_suma_los_siniestros(cliente):
    siniestros = [{"fecha": "2026-03-01", "monto": 100_000, "descripcion": "Choque leve"},
                  {"fecha": "2026-04-01", "monto": 250_000.5, "descripcion": "Hurto de espejo"}]
    cliente.post("/polizas", json=_poliza("POL-IA-000001", siniestros=siniestros))
    cliente.post("/polizas", json=_poliza("POL-IA-000002"))
    r = cliente.get("/resumen")
    assert r.status_code == 200
    assert r.json() == [
        {"numero": "POL-IA-000001", "n_siniestros": 2, "monto_total": 350_000.5},
        {"numero": "POL-IA-000002", "n_siniestros": 0, "monto_total": 0},
    ]


# --- Defecto 2: el test de score no comprobaba lo que dice su nombre -----------

def test_score_de_poliza_recien_creada_queda_registrado(cliente):
    assert cliente.post("/polizas", json=_poliza()).status_code == 201
    r = cliente.post("/score", json={"numero": "POL-IA-000001"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["numero"] == "POL-IA-000001"
    assert 0.0 <= cuerpo["puntaje"] <= 1.0
    assert "error" not in cuerpo
    registradas = cliente.get("/predicciones").json()
    assert [p["numero"] for p in registradas] == ["POL-IA-000001"]


def test_score_de_poliza_inexistente_da_404(cliente):
    assert cliente.post("/score", json={"numero": "POL-NO-EXISTE"}).status_code == 404


def test_las_pruebas_no_tocan_app_db(cliente):
    """El aislamiento se comprueba, no se supone: la base de la app no cambia."""
    app_db = RAIZ / "app.db"
    antes = app_db.stat().st_mtime_ns if app_db.exists() else None
    cliente.post("/polizas", json=_poliza())
    despues = app_db.stat().st_mtime_ns if app_db.exists() else None
    assert antes == despues
