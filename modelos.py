"""Tablas del servicio."""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Poliza(Base):
    __tablename__ = "polizas"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True)
    asegurado: Mapped[str] = mapped_column(String(80))
    tipo: Mapped[str] = mapped_column(String(10))
    prima: Mapped[float] = mapped_column(Float)
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    token_firma: Mapped[str] = mapped_column(String(64))

    siniestros: Mapped[list["Siniestro"]] = relationship(
        back_populates="poliza", cascade="all, delete-orphan")
    predicciones: Mapped[list["Prediccion"]] = relationship(
        back_populates="poliza", cascade="all, delete-orphan")


class Siniestro(Base):
    __tablename__ = "siniestros"

    id: Mapped[int] = mapped_column(primary_key=True)
    poliza_id: Mapped[int] = mapped_column(ForeignKey("polizas.id", ondelete="CASCADE"))
    fecha: Mapped[date] = mapped_column(Date)
    monto: Mapped[float] = mapped_column(Float)
    descripcion: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(10), default="abierto")

    poliza: Mapped["Poliza"] = relationship(back_populates="siniestros")

    @property
    def numero_poliza(self) -> str:
        """Número de la póliza a la que pertenece (para las respuestas)."""
        return self.poliza.numero


class Prediccion(Base):
    __tablename__ = "predicciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    poliza_id: Mapped[int] = mapped_column(ForeignKey("polizas.id", ondelete="CASCADE"))
    puntaje: Mapped[float] = mapped_column(Float)
    alto_riesgo: Mapped[bool]
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    poliza: Mapped["Poliza"] = relationship(back_populates="predicciones")

    @property
    def numero(self) -> str:
        """Número de la póliza puntuada (para las respuestas)."""
        return self.poliza.numero