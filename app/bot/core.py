"""
app/bot/core.py - Funzioni condivise per tutti i comandi del bot Telegram FTTH.

Contiene:
- get_db_session(): context manager per sessione DB
- find_technician(): cerca tecnico per telegram_id
- KEYBOARD: tastiera comandi standard
- reply_error(): risposta errore rapida
"""

import logging
from contextlib import contextmanager
from telegram import ReplyKeyboardMarkup
from app.database import SessionLocal
from app.models.models import Technician

logger = logging.getLogger("app.bot")

# Tastiera standard visibile a tutti i tecnici
# Organizzata per flusso di lavoro: prima vedi → poi agisci → poi chiudi
KEYBOARD = ReplyKeyboardMarkup(
    [["/miei_lavori", "/accetta"],
     ["/modem", "/chiudi"],
     ["/sospendi", "/rifiuta"],
     ["/posizione", "/sos", "/help"]],
    one_time_keyboard=False,
    resize_keyboard=True,
)


@contextmanager
def get_db_session():
    """Context manager per sessione SQLAlchemy."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def find_technician(db, telegram_id: str) -> Technician | None:
    """Cerca un tecnico per telegram_id. Ritorna None se non trovato."""
    return db.query(Technician).filter(
        Technician.telegram_id == telegram_id
    ).first()
