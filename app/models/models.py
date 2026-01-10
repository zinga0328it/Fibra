from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, LargeBinary, Boolean, UniqueConstraint, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

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
    # relation to documents that created/updated this work
    documents = relationship("Document", secondary="document_applied_works", back_populates="applied_works")
    
    # ONT/Modem relationships and flags
    ont = relationship("ONT", back_populates="work", uselist=False)
    modem = relationship("Modem", back_populates="work", uselist=False)
    
    # Equipment requirements flags
    requires_ont = Column(Boolean, default=False)
    requires_modem = Column(Boolean, default=False)
    
    # Delivery tracking
    ont_delivered = Column(Boolean, default=False)
    modem_delivered = Column(Boolean, default=False)
    
    # Additional costs
    ont_cost = Column(Float, default=0.0)
    modem_cost = Column(Float, default=0.0)

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


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    mime = Column(String, nullable=True)
    content = Column(LargeBinary)
    uploaded_at = Column(DateTime)
    parsed = Column(Boolean, default=False)
    parsed_data = Column(JSON, nullable=True)
    applied_work_id = Column(Integer, ForeignKey("works.id"), nullable=True)

    applied_work = relationship("Work", foreign_keys=[applied_work_id])
    # Many-to-many relation to track which works this document applied
    applied_works = relationship("Work", secondary="document_applied_works", back_populates="documents")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="backoffice")
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)

    technician = relationship("Technician")


class DocumentAppliedWork(Base):
    __tablename__ = 'document_applied_works'
    __table_args__ = (UniqueConstraint('document_id', 'work_id', name='uq_document_work'),)
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    work_id = Column(Integer, ForeignKey('works.id'))
    applied_at = Column(DateTime)


class ONT(Base):
    __tablename__ = "onts"

    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(String, unique=True, index=True, nullable=False)
    model = Column(String, nullable=False)
    manufacturer = Column(String)
    status = Column(String, default="available")  # available, assigned, installed, faulty
    work_id = Column(Integer, ForeignKey("works.id"), nullable=True)
    assigned_date = Column(DateTime, nullable=True)
    installed_at = Column(DateTime, nullable=True)
    returned_date = Column(DateTime, nullable=True)
    
    # Network configuration
    pon_port = Column(String)
    vlan_id = Column(Integer)
    ip_address = Column(String)
    
    # Technical notes
    installation_notes = Column(Text)
    technician_notes = Column(Text)
    
    location = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    work = relationship("Work", back_populates="ont")


class Modem(Base):
    __tablename__ = "modems"

    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(String, unique=True, index=True, nullable=False)
    model = Column(String, nullable=False)
    type = Column(String, nullable=False)  # adsl, vdsl, fiber, etc.
    manufacturer = Column(String)
    status = Column(String, default="available")  # available, assigned, installed, faulty
    work_id = Column(Integer, ForeignKey("works.id"), nullable=True)
    
    # Configuration details
    wifi_ssid = Column(String)
    wifi_password = Column(String)
    admin_username = Column(String, default="admin")
    admin_password = Column(String)
    
    # ONT synchronization
    sync_method = Column(String)  # bridge, pppoe, dhcp
    sync_config = Column(JSON)  # Detailed configuration
    
    # Status tracking
    configured_date = Column(DateTime, nullable=True)
    installed_at = Column(DateTime, nullable=True)
    
    # Notes
    configuration_notes = Column(Text)
    installation_notes = Column(Text)
    
    location = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    work = relationship("Work", back_populates="modem")


class ONTModemSync(Base):
    __tablename__ = "ont_modem_sync"

    id = Column(Integer, primary_key=True, index=True)
    ont_id = Column(Integer, ForeignKey("onts.id"), nullable=False)
    modem_id = Column(Integer, ForeignKey("modems.id"), nullable=False)
    work_id = Column(Integer, ForeignKey("works.id"), nullable=False)
    sync_method = Column(String, nullable=False)  # pppoe, dhcp, static, bridge
    sync_config = Column(JSON, nullable=True)  # detailed configuration
    wifi_ssid = Column(String, nullable=True)
    wifi_password = Column(String, nullable=True)
    installation_notes = Column(Text)
    technician_notes = Column(Text)
    sync_status = Column(String, default="pending")  # pending, completed, failed
    synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ont = relationship("ONT")
    modem = relationship("Modem")
    work = relationship("Work")

