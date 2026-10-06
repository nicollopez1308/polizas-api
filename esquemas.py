"""Esquemas de entrada."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _normalizar_nombre(v: str) -> str:
    """Quita espacios sobrantes y pone el nombre con mayúscula inicial."""
    return " ".join(v.split()).title()


class SiniestroEntrada(BaseModel):
    fecha: date
    monto: float = Field(gt=0, description="Monto reclamado, en pesos")
    descripcion: str = Field(min_length=3, max_length=200)
    estado: str = "abierto"


class PolizaEntrada(BaseModel):
    numero: str = Field(min_length=8, max_length=20, description="Formato POL-AAAA-NNNNN")
    asegurado: str = Field(min_length=3, max_length=80)
    tipo: str = Field(description="auto, hogar o vida")
    prima: float = Field(gt=0, description="Prima anual, en pesos")
    fecha_inicio: date
    fecha_fin: date
    siniestros: list[SiniestroEntrada] = Field(
        default_factory=list, description="Siniestros ya declarados"
    )

    @field_validator("asegurado")
    @classmethod
    def normalizar_asegurado(cls, v: str) -> str:
        return _normalizar_nombre(v)

    @model_validator(mode="after")
    def validar_fechas(self) -> "PolizaEntrada":
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
        return self


class PolizaActualizacion(BaseModel):
    asegurado: Optional[str] = Field(default=None, min_length=3, max_length=80)
    tipo: Optional[str] = None
    prima: Optional[float] = Field(default=None, gt=0)
    fecha_fin: Optional[date] = None

    @field_validator("asegurado")
    @classmethod
    def normalizar_asegurado(cls, v: Optional[str]) -> Optional[str]:
        return _normalizar_nombre(v) if v is not None else v


class PuntuacionEntrada(BaseModel):
    numero: str = Field(min_length=8, max_length=20)
    

# ---------------------------------------------------------------------------
# Esquemas de salida: deciden qué campos salen de la API. Lo que no esté aquí
# (por ejemplo token_firma) no se responde nunca. from_attributes=True permite
# construirlos directamente desde los objetos de SQLAlchemy.
# ---------------------------------------------------------------------------

class SiniestroSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: date
    monto: float
    descripcion: str
    estado: str


class SiniestroDetalle(SiniestroSalida):
    poliza_id: int
    numero_poliza: str


class PolizaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    asegurado: str
    tipo: str
    prima: float
    fecha_inicio: date
    fecha_fin: date
    siniestros: list[SiniestroSalida]


class ResumenSalida(BaseModel):
    numero: str
    n_siniestros: int
    monto_total: float


class PuntuacionSalida(BaseModel):
    numero: str
    puntaje: float
    alto_riesgo: bool


class PrediccionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    poliza_id: int
    numero: str
    puntaje: float
    alto_riesgo: bool
    creado_en: datetime


class SaludSalida(BaseModel):
    estado: str
    base_de_datos: str