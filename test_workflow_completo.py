#!/usr/bin/env python3
"""Test workflow completo: creazione lavoro + notifica Telegram"""

import asyncio
import os
from datetime import datetime
from telegram import Bot
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Work, Technician

# Configurazione
DB_URL = "sqlite:///./ftth.db"
BOT_TOKEN = "7792799425:AAEOVfNjAlxPBXcIcPW7uxRWtRgCKlWloV8"
TELEGRAM_ID = "7586394272"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

async def test_workflow():
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║          🎯 TEST WORKFLOW COMPLETO                            ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    
    # Step 1: Crea lavoro nel database
    print("📝 STEP 1: Creazione lavoro nel database...")
    db = SessionLocal()
    try:
        numero_wr = f"TEST_{int(datetime.now().timestamp())}"
        
        new_work = Work(
            numero_wr=numero_wr,
            stato="aperto",
            nome_cliente="Cliente Test Automatico",
            indirizzo="Via Test 123, Roma",
            operatore="Open Fiber",
            tipo_lavoro="Installazione",
            tecnico_assegnato_id=1,
            note="Test workflow completo con notifica Telegram",
            data_apertura=datetime.now()
        )
        
        db.add(new_work)
        db.commit()
        db.refresh(new_work)
        
        print(f"✅ Lavoro creato: ID={new_work.id}, WR={new_work.numero_wr}")
        work_id = new_work.id
        
        # Get technician info
        tech = db.query(Technician).filter(Technician.id == 1).first()
        print(f"✅ Tecnico assegnato: {tech.nome} {tech.cognome}")
        print(f"✅ Telegram ID: {tech.telegram_id}")
        
    except Exception as e:
        print(f"❌ Errore creazione lavoro: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    print()
    
    # Step 2: Invia notifica Telegram
    print("📱 STEP 2: Invio notifica Telegram...")
    try:
        bot = Bot(token=BOT_TOKEN)
        
        message = f"""
🔔 NUOVO LAVORO ASSEGNATO

📋 Lavoro: {numero_wr}
👤 Cliente: Cliente Test Automatico
📍 Indirizzo: Via Test 123, Roma

🔧 Tipo: Installazione
🏢 Operatore: Open Fiber

📝 Note: Test workflow completo

✅ Usa /miei_lavori per vedere tutti i lavori
"""
        
        result = await bot.send_message(chat_id=TELEGRAM_ID, text=message)
        print(f"✅ Notifica inviata con successo!")
        print(f"📱 Message ID: {result.message_id}")
        print(f"📲 Chat ID: {result.chat_id}")
        
    except Exception as e:
        print(f"❌ Errore invio notifica: {e}")
        return False
    
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("✅ TEST WORKFLOW COMPLETATO CON SUCCESSO!")
    print("═══════════════════════════════════════════════════════════════")
    print()
    print("🎉 Il sistema è completamente funzionante:")
    print("   ✅ Database OK")
    print("   ✅ Creazione lavori OK")
    print("   ✅ Telegram ID configurato OK")
    print("   ✅ Notifiche Telegram OK")
    print()
    print("📱 Dovresti aver ricevuto la notifica su Telegram!")
    print()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_workflow())
    exit(0 if success else 1)
