from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True, index=True)
    numero_wr = Column(String, unique=True, index=True)
    operatore = Column(String)
    indirizzo = Column(String)
    nome_cliente = Column(String)
    tipo_lavoro = Column(String)  # attivazione, guasto, manutenzione
    stato = Column(String, default="aperto")  # aperto, in_corso, sospeso, chiuso
    data_apertura = Column(DateTime)
    data_chiusura = Column(DateTime, nullable=True)
    tecnico_assegnato_id = Column(Integer, ForeignKey("technicians.id"))
    tecnico_chiusura_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    note = Column(String, nullable=True)
    extra_fields = Column(JSON, nullable=True)

    tecnico_assegnato = relationship("Technician", foreign_keys=[tecnico_assegnato_id])
    tecnico_chiusura = relationship("Technician", foreign_keys=[tecnico_chiusura_id])

class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    cognome = Column(String)
    telefono = Column(String)
    squadra_id = Column(Integer, ForeignKey("teams.id"))
    telegram_id = Column(String, nullable=True)

    squadra = relationship("Team")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)

class WorkEvent(Base):
    __tablename__ = "work_events"

    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey("works.id"))
    timestamp = Column(DateTime)
    event_type = Column(String)  # assigned, status_change, etc.
    description = Column(String)
    user_id = Column(Integer, ForeignKey("technicians.id"))