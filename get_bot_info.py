#!/usr/bin/env python3
"""Script per ottenere il tuo Telegram ID"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

async def get_me():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN non trovato")
        return
    
    bot = Bot(token=token)
    
    print("🤖 Informazioni Bot:\n")
    me = await bot.get_me()
    print(f"✅ Nome: {me.first_name}")
    print(f"✅ Username: @{me.username}")
    print(f"✅ ID: {me.id}")
    print()
    print("="*60)
    print("\n📱 PER OTTENERE IL TUO TELEGRAM ID:")
    print(f"\n1. Apri Telegram e cerca: @{me.username}")
    print("2. Invia /start al bot")
    print("3. Poi esegui questo comando per vedere chi ha scritto:\n")
    print("   python scripts/get_bot_updates.py")
    print("\nOPPURE usa @userinfobot su Telegram per vedere il tuo ID")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(get_me())
