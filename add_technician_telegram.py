#!/usr/bin/env python3
"""
Script per aggiungere un tecnico con Telegram ID

Uso:
    python add_technician_telegram.py
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:6030"

def add_technician():
    print("=" * 60)
    print("🔧 AGGIUNGI TECNICO CON TELEGRAM")
    print("=" * 60)
    print()
    
    # Input dati tecnico
    nome = input("📝 Nome: ").strip()
    cognome = input("📝 Cognome: ").strip()
    telefono = input("📞 Telefono: ").strip()
    
    # Mostra squadre disponibili
    print("\n📋 Caricamento squadre...")
    try:
        resp = requests.get(f"{API_BASE}/teams/")
        teams = resp.json()
        if not teams:
            print("❌ Nessuna squadra trovata! Crea prima una squadra.")
            return
        
        print("\nSquadre disponibili:")
        for team in teams:
            print(f"  {team['id']} - {team['nome']}")
        
        squadra_id = int(input("\n🔢 ID Squadra: ").strip())
    except Exception as e:
        print(f"❌ Errore caricamento squadre: {e}")
        return
    
    # Telegram ID (opzionale)
    print("\n" + "=" * 60)
    print("📱 TELEGRAM ID (OPZIONALE)")
    print("=" * 60)
    print("\nPer ottenere il Telegram ID del tecnico:")
    print("1. Il tecnico apre Telegram")
    print("2. Cerca @userinfobot")
    print("3. Invia /start")
    print("4. Copia l'ID numerico")
    print()
    
    telegram_id = input("📱 Telegram ID (lascia vuoto per saltare): ").strip()
    if not telegram_id:
        telegram_id = None
    
    # Crea il tecnico
    payload = {
        "nome": nome,
        "cognome": cognome,
        "telefono": telefono,
        "squadra_id": squadra_id
    }
    
    if telegram_id:
        payload["telegram_id"] = telegram_id
    
    print("\n⏳ Creazione tecnico...")
    
    try:
        resp = requests.post(
            f"{API_BASE}/technicians/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if resp.status_code == 200 or resp.status_code == 201:
            tech = resp.json()
            print("\n" + "=" * 60)
            print("✅ TECNICO CREATO CON SUCCESSO!")
            print("=" * 60)
            print(f"\n🆔 ID: {tech['id']}")
            print(f"👤 Nome: {tech['nome']} {tech['cognome']}")
            print(f"📞 Telefono: {tech['telefono']}")
            print(f"👥 Squadra: {tech['squadra']['nome'] if tech.get('squadra') else 'N/A'}")
            print(f"📱 Telegram ID: {tech.get('telegram_id') or 'Non configurato'}")
            
            if telegram_id:
                print("\n✅ Il tecnico può ora usare il bot Telegram!")
                print("   Deve cercare il bot e inviare /start")
            else:
                print("\n⚠️  Per abilitare le notifiche Telegram:")
                print("   1. Ottieni il Telegram ID del tecnico")
                print("   2. Aggiornalo tramite l'interfaccia web o API")
        else:
            print(f"\n❌ Errore: {resp.status_code}")
            print(resp.text)
    
    except Exception as e:
        print(f"\n❌ Errore durante la creazione: {e}")

if __name__ == "__main__":
    try:
        add_technician()
    except KeyboardInterrupt:
        print("\n\n👋 Operazione annullata")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
