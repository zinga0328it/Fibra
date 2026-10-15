#!/usr/bin/env python3
"""Utility indipendente per abilitare archiviazione dei lavori e pulizia periodica.

Questo file non tocca alcun modulo dell'applicazione: è un tool standalone che può
essere eseguito da cron sul server.

Funzionalità:

* se la colonna `archived` non esiste nella tabella `works`, la crea automaticamente
  (utile per aggiornare il database esistente senza interventi manuali); questo
  accade una sola volta.
* imposta il flag `archived=1` per tutti i lavori con stato 'sospeso' e con
  data_apertura più vecchia di 14 giorni.

Uso:
    $ ./scripts/auto_archive.py

Esempio di cron (ogni 2 settimane):
    0 3 */14 * * /home/aaa/fibra/temp_venv/bin/python /home/aaa/fibra/scripts/auto_archive.py >> /var/log/ftth_archive.log 2>&1

"""

import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'ftth.db')


def ensure_column(conn):
    cur = conn.cursor()
    # controlla se esiste
    cur.execute("PRAGMA table_info(works)")
    columns = [row[1] for row in cur.fetchall()]
    if 'archived' not in columns:
        print('Aggiungo colonna archived alla tabella works')
        cur.execute('ALTER TABLE works ADD COLUMN archived INTEGER DEFAULT 0')
        conn.commit()
    else:
        print('Colonna archived già presente')


def archive_old():
    now = datetime.utcnow()
    cutoff = now - timedelta(days=14)
    cur = conn.cursor()
    cur.execute(
        "UPDATE works SET archived=1 WHERE stato='sospeso' AND archived=0 AND data_apertura < ?",
        (cutoff.isoformat(),)
    )
    changed = cur.rowcount
    conn.commit()
    if changed:
        print(f'Archiviati {changed} lavori (>14 giorni sospesi)')
    else:
        print('Nessun lavoro sospeso da archiviare')


if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"Database non trovato: {DB_PATH}")
        exit(1)
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_column(conn)
        archive_old()
    finally:
        conn.close()
