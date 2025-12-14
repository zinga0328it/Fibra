#!/usr/bin/env python3
"""
Script per aggiornare il Telegram ID di un tecnico esistente

Uso:
    python update_technician_telegram.py
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:6030"

def update_telegram_id():
    print("=" * 60)
    print("📱 AGGIORNA TELEGRAM ID TECNICO")
    print("=" * 60)
    print()
    
    # Mostra tecnici esistenti
    print("📋 Caricamento tecnici...")
    try:
        resp = requests.get(f"{API_BASE}/technicians/")
        technicians = resp.json()
        
        if not technicians:
            print("❌ Nessun tecnico trovato! Crea prima un tecnico.")
            return
        
        print("\nTecnici disponibili:")
        print("-" * 60)
        for tech in technicians:
            telegram_status = f"📱 {tech.get('telegram_id')}" if tech.get('telegram_id') else "❌ Non configurato"
            print(f"{tech['id']}: {tech['nome']} {tech['cognome']} - {telegram_status}")
        print("-" * 60)
        
        tech_id = int(input("\n🔢 ID Tecnico da aggiornare: ").strip())
        
        # Trova il tecnico
        selected_tech = next((t for t in technicians if t['id'] == tech_id), None)
        if not selected_tech:
            print("❌ Tecnico non trovato!")
            return
        
        print(f"\n✅ Selezionato: {selected_tech['nome']} {selected_tech['cognome']}")
        
    except Exception as e:
        print(f"❌ Errore caricamento tecnici: {e}")
        return
    
    # Telegram ID
    print("\n" + "=" * 60)
    print("📱 NUOVO TELEGRAM ID")
    print("=" * 60)
    print("\nPer ottenere il Telegram ID:")
    print("1. Il tecnico apre Telegram")
    print("2. Cerca @userinfobot")
    print("3. Invia /start")
    print("4. Copia l'ID numerico")
    print("\nOPPURE:")
    print("  python scripts/get_bot_updates.py")
    print()
    
    telegram_id = input("📱 Nuovo Telegram ID: ").strip()
    
    if not telegram_id:
        print("❌ Telegram ID obbligatorio!")
        return
    
    # Aggiorna il tecnico via PATCH
    print("\n⏳ Aggiornamento in corso...")
    
    try:
        resp = requests.patch(
            f"{API_BASE}/technicians/{tech_id}",
            json={"telegram_id": telegram_id},
            headers={"Content-Type": "application/json"}
        )
        
        if resp.status_code == 200:
            tech = resp.json()
            print("\n" + "=" * 60)
            print("✅ TELEGRAM ID AGGIORNATO!")
            print("=" * 60)
            print(f"\n🆔 ID Tecnico: {tech['id']}")
            print(f"👤 Nome: {tech['nome']} {tech['cognome']}")
            print(f"📱 Telegram ID: {tech.get('telegram_id')}")
            print("\n✅ Il tecnico può ora usare il bot Telegram!")
            print("   Deve cercare il bot e inviare /start")
        else:
            print(f"\n❌ Errore: {resp.status_code}")
            print(resp.text)
    
    except Exception as e:
        print(f"\n❌ Errore durante l'aggiornamento: {e}")

if __name__ == "__main__":
    try:
        update_telegram_id()
    except KeyboardInterrupt:
        print("\n\n👋 Operazione annullata")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
