"""
app/utils/rate_limiter.py - Anti-flood / Rate limiter per il bot e le API.

Limita il numero di richieste per utente/IP in una finestra temporale.
Usa un dizionario in-memory (nessuna dipendenza esterna).
Thread-safe tramite Lock.
"""

import time
import threading
from collections import defaultdict
from functools import wraps
from fastapi import HTTPException, Request
import logging

logger = logging.getLogger("app.utils.rate_limiter")


class RateLimiter:
    """
    Rate limiter in-memory basato su sliding window.

    Parametri:
        max_requests: numero massimo di richieste nella finestra
        window_seconds: durata della finestra in secondi
        cleanup_interval: ogni quante richieste pulire le entry scadute
    """

    def __init__(self, max_requests: int = 20, window_seconds: int = 60, cleanup_interval: int = 100):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.cleanup_interval = cleanup_interval
        self._requests = defaultdict(list)  # key -> [timestamp, ...]
        self._lock = threading.Lock()
        self._call_count = 0

    def is_allowed(self, key: str) -> bool:
        """
        Controlla se la richiesta è permessa per la chiave data.
        Ritorna True se ok, False se rate limited.
        """
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            # Rimuovi timestamp scaduti per questa chiave
            self._requests[key] = [t for t in self._requests[key] if t > cutoff]

            if len(self._requests[key]) >= self.max_requests:
                logger.warning("Rate limit hit for key=%s (%d/%d in %ds)",
                               key, len(self._requests[key]), self.max_requests, self.window_seconds)
                return False

            self._requests[key].append(now)

            # Cleanup periodico delle chiavi vuote
            self._call_count += 1
            if self._call_count % self.cleanup_interval == 0:
                self._cleanup(now)

            return True

    def remaining(self, key: str) -> int:
        """Quante richieste rimangono per questa chiave."""
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            active = [t for t in self._requests[key] if t > cutoff]
            return max(0, self.max_requests - len(active))

    def reset(self, key: str):
        """Reset del contatore per una chiave."""
        with self._lock:
            self._requests.pop(key, None)

    def _cleanup(self, now: float):
        """Rimuovi chiavi con tutti i timestamp scaduti."""
        cutoff = now - self.window_seconds
        expired_keys = [k for k, v in self._requests.items() if not v or all(t <= cutoff for t in v)]
        for k in expired_keys:
            del self._requests[k]


# ============================================================
# Istanze pre-configurate
# ============================================================

# Bot Telegram: max 15 comandi al minuto per utente
telegram_limiter = RateLimiter(max_requests=15, window_seconds=60)

# Bot Telegram: max 3 comandi identici in 10 secondi (anti doppio-click)
telegram_cmd_limiter = RateLimiter(max_requests=3, window_seconds=10)

# API generiche: max 60 richieste al minuto per IP
api_limiter = RateLimiter(max_requests=60, window_seconds=60)

# Webhook: max 30 chiamate al minuto globali (protezione DDoS)
webhook_global_limiter = RateLimiter(max_requests=120, window_seconds=60)


# ============================================================
# Helper functions
# ============================================================

def check_telegram_flood(telegram_id: str, command: str = None) -> str | None:
    """
    Controlla se un utente Telegram sta floodando.

    Returns:
        None se ok, stringa con messaggio di errore se rate limited.
    """
    # Check globale per utente
    if not telegram_limiter.is_allowed(f"tg:{telegram_id}"):
        remaining = telegram_limiter.remaining(f"tg:{telegram_id}")
        return "⚠️ Troppi messaggi! Aspetta un minuto prima di usare altri comandi."

    # Check anti doppio-click per comando specifico
    if command:
        key = f"tg:{telegram_id}:{command}"
        if not telegram_cmd_limiter.is_allowed(key):
            return "⏳ Comando già inviato, attendi qualche secondo..."

    return None


def check_api_flood(client_ip: str) -> bool:
    """
    Controlla se un IP sta floodando le API.
    Returns True se ok, False se rate limited.
    """
    return api_limiter.is_allowed(f"api:{client_ip}")
