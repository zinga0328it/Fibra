from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict
from datetime import datetime

class TeamCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=100)

class TeamOut(BaseModel):
    id: int
    nome: str
    model_config = ConfigDict(from_attributes=True)

class TechnicianCreate(BaseModel):
    nome: str = Field(min_length=1)
    cognome: str = Field(min_length=1)
    telefono: str
    squadra_id: int

    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v: str):
        import re
        if not re.match(r"^[0-9\+\-\s]{6,20}$", v):
            raise ValueError('telefono must be numeric and 6-20 chars')
        return v

class TechnicianOut(BaseModel):
    id: int
    nome: str
    cognome: str
    telefono: str
    squadra: Optional[TeamOut]
    model_config = ConfigDict(from_attributes=True)

class WorkCreate(BaseModel):
    numero_wr: str = Field(min_length=1, max_length=64)
    operatore: str = Field(min_length=1)
    indirizzo: str = Field(min_length=1)
    nome_cliente: str = Field(min_length=1)
    tipo_lavoro: str = Field(default="attivazione")
    note: Optional[str] = None
    extra_fields: Optional[Dict] = Field(default_factory=dict)

    @field_validator('numero_wr')
    @classmethod
    def validate_numero_wr(cls, v: str):
        import re
        if not re.match(r"^[A-Za-z0-9\-_/]+$", v):
            raise ValueError('numero_wr invalid format')
        return v

    @field_validator('tipo_lavoro')
    @classmethod
    def validate_tipo_lavoro(cls, v: str):
        if v not in {"attivazione", "guasto", "manutenzione"}:
            raise ValueError('Invalid tipo_lavoro')
        return v

class WorkOut(BaseModel):
    id: int
    numero_wr: str
    operatore: str
    indirizzo: str
    nome_cliente: str
    tipo_lavoro: str
    stato: str
    data_apertura: Optional[datetime]
    data_chiusura: Optional[datetime]
    tecnico_assegnato: Optional[TechnicianOut]
    extra_fields: Optional[Dict] = None

    model_config = ConfigDict(from_attributes=True)

class WorkStatusUpdate(BaseModel):
    status: str

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str):
        if v not in {"aperto", "in_corso", "sospeso", "chiuso"}:
            raise ValueError('Invalid status')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str):
        if v not in {"admin", "tecnico", "backoffice"}:
            raise ValueError('Invalid role')
        return v
