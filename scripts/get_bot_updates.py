#!/usr/bin/env python3
"""Script per vedere chi ha scritto al bot"""

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
    
    print("📱 Ultimi messaggi ricevuti dal bot:\n")
    print("="*70)
    
    updates = await bot.get_updates()
    
    if not updates:
        print("❌ Nessun messaggio trovato")
        print("\nAssicurati che:")
        print("1. Il tecnico abbia cercato il bot su Telegram")
        print("2. Il tecnico abbia inviato /start al bot")
        return
    
    for update in updates[-10:]:  # Mostra ultimi 10
        if update.message:
            user = update.message.from_user
            text = update.message.text or ""
            print(f"\n👤 Nome: {user.first_name} {user.last_name or ''}")
            print(f"🆔 Telegram ID: {user.id}")
            print(f"📝 Username: @{user.username or 'N/A'}")
            print(f"💬 Messaggio: {text}")
            print("-"*70)
    
    print("\n✅ Copia l'ID numerico da usare nel sistema!")

if __name__ == "__main__":
    asyncio.run(get_updates())
