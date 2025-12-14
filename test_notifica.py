#!/usr/bin/env python3
import os
import asyncio
from telegram import Bot

async def send_test():
    token = "7792799425:AAEOVfNjAlxPBXcIcPW7uxRWtRgCKlWloV8"
    test_id = "7586394272"
    bot = Bot(token=token)
    
    message = """🎉 TEST NOTIFICA TELEGRAM

✅ Sistema FTTH configurato correttamente!
📱 Bot: @MaioriDealsBot
🆔 Tuo Telegram ID: 7586394272

🔔 Ora puoi ricevere notifiche per:
• Nuovi lavori assegnati
• Aggiornamenti lavori
• Messaggi dal sistema

🤖 Comandi disponibili:
/start - Avvia bot
/miei_lavori - Vedi lavori assegnati
/help - Mostra aiuto

✅ Sistema pronto!"""
    
    try:
        result = await bot.send_message(chat_id=test_id, text=message)
        print("✅ MESSAGGIO INVIATO CON SUCCESSO!")
        print(f"📱 Controlla Telegram (@MaioriDealsBot)")
        print(f"📝 Message ID: {result.message_id}")
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    asyncio.run(send_test())
