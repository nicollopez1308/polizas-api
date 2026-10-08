"""
Pólizas API — Gestión de pólizas y siniestros.
Aseguradora Santo Tomás.
"""
import hashlib
import pickle
from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from config import Settings, get_settings
from database import get_db
from esquemas import (PolizaActualizacion, PolizaEntrada, PolizaSalida, PrediccionSalida,
                      PuntuacionEntrada, PuntuacionSalida, ResumenSalida, SaludSalida,
                      SiniestroDetalle, SiniestroEntrada, SiniestroSalida)
from modelos import Poliza, Prediccion, Siniestro

with open(get_settings().ruta_modelo, "rb") as fh:
    modelo = pickle.load(fh)

app = FastAPI(title="Pólizas API", version="1.0.0")


def firmar(numero: str, secreto: str) -> str:
    return hashlib.sha256(f"{numero}:{secreto}".encode()).hexdigest()


def _buscar_poliza(db: Session, id_poliza: int) -> Poliza:
    """Devuelve la póliza o responde 404 si no existe."""
    poliza = db.get(Poliza, id_poliza)
    if poliza is None:
        raise HTTPException(status_code=404, detail=f"no existe la póliza {id_poliza}")
    return poliza


@app.get("/health", response_model=SaludSalida)
def salud(db: Session = Depends(get_db)):
    """Sonda de salud: el servicio responde y dice si la base de datos contesta."""
    try:
        db.execute(text("SELECT 1"))
        base_de_datos = "ok"
    except SQLAlchemyError:
        base_de_datos = "sin conexión"
    return {"estado": "ok", "base_de_datos": base_de_datos}


@app.post("/polizas", response_model=PolizaSalida, status_code=201)
def crear_poliza(datos: PolizaEntrada, db: Session = Depends(get_db),
                 settings: Settings = Depends(get_settings)):
    poliza = Poliza(**datos.model_dump(exclude={"siniestros"}),
                    token_firma=firmar(datos.numero, settings.secreto_firma))
    poliza.siniestros = [Siniestro(**s.model_dump()) for s in datos.siniestros]
    db.add(poliza)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"ya existe la póliza {datos.numero}")
    db.refresh(poliza)
    return poliza


@app.get("/polizas", response_model=list[PolizaSalida])
def listar_polizas(db: Session = Depends(get_db)):
    # selectinload: 1 consulta para las pólizas + 1 para TODOS sus siniestros (WHERE poliza_id IN ...).
    consulta = select(Poliza).options(selectinload(Poliza.siniestros)).order_by(Poliza.id)
    return db.scalars(consulta).all()


@app.get("/polizas/{id_poliza}", response_model=PolizaSalida)
def obtener_poliza(id_poliza: int, db: Session = Depends(get_db)):
    # lazy a propósito: es UNA póliza, así que sus siniestros cuestan 1 consulta más,
    # tenga la base 10 pólizas o 2000. Cargarlos por adelantado no ahorra nada medible.
    return _buscar_poliza(db, id_poliza)


@app.put("/polizas/{id_poliza}", response_model=PolizaSalida)
def actualizar_poliza(id_poliza: int, datos: PolizaActualizacion, db: Session = Depends(get_db)):
    poliza = _buscar_poliza(db, id_poliza)
    # Solo los campos que el cliente envió (y que no vienen en null).
    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    for campo, valor in cambios.items():
        setattr(poliza, campo, valor)
    if poliza.fecha_fin <= poliza.fecha_inicio:
        db.rollback()
        raise HTTPException(status_code=422, detail="fecha_fin debe ser posterior a fecha_inicio")
    db.commit()
    db.refresh(poliza)
    return poliza


@app.post("/polizas/{id_poliza}/siniestros", response_model=SiniestroSalida, status_code=201)
def declarar_siniestro(id_poliza: int, datos: SiniestroEntrada, db: Session = Depends(get_db)):
    poliza = _buscar_poliza(db, id_poliza)
    siniestro = Siniestro(**datos.model_dump(), poliza=poliza)
    db.add(siniestro)
    db.commit()
    db.refresh(siniestro)
    return siniestro


@app.get("/siniestros", response_model=list[SiniestroDetalle])
def listar_siniestros(db: Session = Depends(get_db)):
    # joinedload: cada siniestro trae su póliza en la MISMA consulta (JOIN). Es una relación
    # muchos-a-uno, así que el JOIN no repite filas.
    consulta = select(Siniestro).options(joinedload(Siniestro.poliza)).order_by(Siniestro.id)
    return db.scalars(consulta).all()


@app.get("/resumen", response_model=list[ResumenSalida])
def resumen(db: Session = Depends(get_db)):
    # agregada: la base cuenta y suma con GROUP BY; no se trae ni un solo objeto Siniestro.
    consulta = (
        select(Poliza.numero,
               func.count(Siniestro.id).label("n_siniestros"),
               func.coalesce(func.sum(Siniestro.monto), 0).label("monto_total"))
        .outerjoin(Siniestro)
        .group_by(Poliza.id)
        .order_by(Poliza.id)
    )
    return [{"numero": f.numero, "n_siniestros": f.n_siniestros,
             "monto_total": round(f.monto_total, 2)} for f in db.execute(consulta)]


@app.post("/score", response_model=PuntuacionSalida)
def puntuar(datos: PuntuacionEntrada, db: Session = Depends(get_db),
            settings: Settings = Depends(get_settings)):
    poliza = db.scalar(select(Poliza).where(Poliza.numero == datos.numero))
    if poliza is None:
        raise HTTPException(status_code=404, detail=f"no existe la póliza {datos.numero}")
    rasgos = [[poliza.prima, len(poliza.siniestros), sum(s.monto for s in poliza.siniestros),
               (date.today() - poliza.fecha_inicio).days]]
    puntaje = float(modelo.predict_proba(rasgos)[0][1])
    prediccion = Prediccion(poliza_id=poliza.id, puntaje=puntaje,
                            alto_riesgo=puntaje > settings.umbral_alto_riesgo)
    db.add(prediccion)
    db.commit()
    return {"numero": poliza.numero, "puntaje": round(puntaje, 4),
            "alto_riesgo": prediccion.alto_riesgo}


@app.get("/predicciones", response_model=list[PrediccionSalida])
def listar_predicciones(db: Session = Depends(get_db)):
    return db.scalars(select(Prediccion).order_by(Prediccion.id)).all()