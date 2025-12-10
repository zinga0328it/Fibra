#!/usr/bin/env python3
"""Script per vedere gli ultimi messaggi ricevuti dal bot"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

async def get_updates():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN non trovato")
        return
    
    bot = Bot(token=token)
    
    print("📨 Ultimi messaggi ricevuti dal bot:\n")
    print("="*60)
    
    try:
        updates = await bot.get_updates(limit=10)
        
        if not updates:
            print("\n⚠️  Nessun messaggio recente trovato!")
            print("\n💡 Per testare:")
            print("1. Apri Telegram")
            print("2. Cerca @Flowers007bot")
            print("3. Invia /start")
            print("4. Ri-esegui questo script")
            return
        
        for update in updates:
            if update.message:
                msg = update.message
                user = msg.from_user
                
                print(f"\n👤 Utente:")
                print(f"   Nome: {user.first_name} {user.last_name or ''}")
                print(f"   Username: @{user.username or 'N/A'}")
                print(f"   🎯 TELEGRAM ID: {user.id}")
                print(f"\n💬 Messaggio: {msg.text}")
                print(f"   Data: {msg.date}")
                print("-"*60)
        
        print("\n✅ Per usare questi utenti nel database:")
        print("Aggiorna la tabella technicians con il TELEGRAM ID dell'utente")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    asyncio.run(get_updates())
