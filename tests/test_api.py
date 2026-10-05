"""Pruebas propias del servicio (B8).

    python -m pytest tests/test_api.py -v

Cada test usa su propia base SQLite temporal y vacía: get_db se sustituye
con app.dependency_overrides, así que app.db nunca se toca y pytest puede
correrse varias veces seguidas.
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

# Antes de importar la app: que nunca apunte a app.db, ni siquiera al arrancar.
os.environ["DATABASE_URL"] = f"sqlite:///{Path(tempfile.gettempdir()) / 'polizas_import.db'}"

import modelos  # noqa: E402,F401  (registra las tablas en Base.metadata)
from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402


def _poliza(**cambios):
    """Póliza válida de ejemplo; cambios reemplaza los campos indicados."""
    datos = {
        "numero": "POL-2026-00001",
        "asegurado": "Prueba Interna",
        "tipo": "auto",
        "prima": 1_000_000,
        "fecha_inicio": "2026-01-01",
        "fecha_fin": "2026-12-31",
    }
    datos.update(cambios)
    return datos


@pytest.fixture
def cliente(tmp_path):
    """Cliente de pruebas sobre una base temporal nueva para cada test."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'prueba.db'}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def _claves_foraneas(conexion, _registro):
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SesionPrueba = sessionmaker(bind=engine, autoflush=False)

    def _get_db_prueba():
        db = SesionPrueba()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db_prueba
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def test_base_empieza_vacia(cliente):
    r = cliente.get("/polizas")
    assert r.status_code == 200
    assert r.json() == []


def test_crear_poliza_da_201_sin_token(cliente):
    r = cliente.post("/polizas", json=_poliza())
    assert r.status_code == 201
    assert r.json()["numero"] == "POL-2026-00001"
    assert "token_firma" not in r.json()


def test_listar_incluye_la_creada(cliente):
    cliente.post("/polizas", json=_poliza())
    r = cliente.get("/polizas")
    assert any(p["numero"] == "POL-2026-00001" for p in r.json())


def test_asegurado_se_normaliza(cliente):
    r = cliente.post("/polizas", json=_poliza(asegurado="  ana   maria  perez "))
    assert r.json()["asegurado"] == "Ana Maria Perez"


def test_fechas_invertidas_dan_422(cliente):
    r = cliente.post("/polizas", json=_poliza(fecha_inicio="2026-12-31", fecha_fin="2026-01-01"))
    assert r.status_code == 422


def test_siniestro_con_monto_negativo_da_422(cliente):
    siniestro = {"fecha": "2026-03-01", "monto": -5000, "descripcion": "choque"}
    r = cliente.post("/polizas", json=_poliza(siniestros=[siniestro]))
    assert r.status_code == 422


def test_poliza_inexistente_da_404(cliente):
    r = cliente.get("/polizas/99999")
    assert r.status_code == 404