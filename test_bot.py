#!/usr/bin/env python3
"""Script di test per il Bot Telegram FTTH"""

import os
import sys
from dotenv import load_dotenv
from app.database import SessionLocal
from app.models.models import Work, Technician
from app.utils.telegram import send_message_to_telegram

load_dotenv()

def test_bot():
    print("🤖 === TEST BOT TELEGRAM FTTH ===\n")
    
    # Verifica token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN non trovato nel .env")
        return False
    print(f"✅ Token trovato: {token[:20]}...")
    
    # Connessione database
    try:
        db = SessionLocal()
        print("✅ Connessione database OK\n")
    except Exception as e:
        print(f"❌ Errore database: {e}")
        return False
    
    # Lista tecnici
    print("📋 TECNICI NEL DATABASE:")
    techs = db.query(Technician).all()
    if not techs:
        print("⚠️  Nessun tecnico trovato")
        db.close()
        return False
    
    for tech in techs:
        print(f"  • {tech.nome} {tech.cognome}")
        print(f"    ID: {tech.id}")
        print(f"    Telefono: {tech.telefono or 'N/A'}")
        print(f"    Telegram ID: {tech.telegram_id or '❌ NON CONFIGURATO'}")
        print()
    
    # Trova tecnico con telegram_id
    tech_with_telegram = None
    for tech in techs:
        if tech.telegram_id:
            tech_with_telegram = tech
            break
    
    if not tech_with_telegram:
        print("⚠️  Nessun tecnico ha Telegram ID configurato!")
        print("Per testare, aggiungi un telegram_id a un tecnico nel database.")
        db.close()
        return False
    
    print(f"✅ Tecnico selezionato per test: {tech_with_telegram.nome} {tech_with_telegram.cognome}")
    print(f"   Telegram ID: {tech_with_telegram.telegram_id}\n")
    
    # Lista lavori assegnati
    print(f"📦 LAVORI ASSEGNATI A {tech_with_telegram.nome}:")
    works = db.query(Work).filter(Work.tecnico_assegnato_id == tech_with_telegram.id).all()
    if not works:
        print("  Nessun lavoro assegnato")
    else:
        for w in works:
            print(f"  • WR {w.numero_wr} - Stato: {w.stato} - {w.indirizzo or 'N/A'}")
    print()
    
    # Test invio messaggio
    print("📨 TEST INVIO MESSAGGIO TELEGRAM:")
    test_message = f"""🤖 Test Bot FTTH

Ciao {tech_with_telegram.nome}!

Questo è un messaggio di test per verificare che il bot funzioni correttamente.

Comandi disponibili:
/start - Menu principale
/miei_lavori - Vedi i tuoi lavori
/accetta <WR> - Accetta un lavoro
/rifiuta <WR> - Rifiuta un lavoro  
/chiudi <WR> - Chiudi un lavoro
/help - Aiuto

✅ Bot operativo!"""
    
    print(f"Invio a: {tech_with_telegram.telegram_id}")
    result = send_message_to_telegram(tech_with_telegram.telegram_id, test_message)
    
    if result:
        print("✅ Messaggio inviato con successo!")
    else:
        print("❌ Errore nell'invio del messaggio")
    
    db.close()
    return result

if __name__ == "__main__":
    print("\n" + "="*60)
    success = test_bot()
    print("="*60 + "\n")
    
    if success:
        print("✅ Test completato con successo!")
        print("\nOra prova sul tuo Telegram:")
        print("1. Apri il bot")
        print("2. Invia /start")
        print("3. Invia /miei_lavori")
        print("4. Controlla i log con: sudo journalctl -u ftth_bot.service -f")
        sys.exit(0)
    else:
        print("❌ Test fallito - controlla la configurazione")
        sys.exit(1)
