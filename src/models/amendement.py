from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from .base import Base


class Amendement(Base):
    __tablename__ = "amendements"

    uid: Mapped[str] = mapped_column(primary_key=True)
    dataset: Mapped[int]
    signatairesLibelle: Mapped[str] = mapped_column(String(2000))
    dispositif: Mapped[str] = mapped_column(String(5000))
    exposeSommaire: Mapped[str] = mapped_column(String(10000))
    
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=True)