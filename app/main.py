from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.handlers import RotatingFileHandler, SysLogHandler
import os
from dotenv import load_dotenv
from telegram import Bot, BotCommand
from app.utils.bot_commands import set_bot_commands_async, get_token_from_env, BOT_COMMANDS
from app.database import engine
from app.models import models
from pythonjsonlogger import jsonlogger

try:
	models.Base.metadata.create_all(bind=engine)
except Exception as e:
	# If DB isn't available (for example during local development without Postgres), warn and continue
	import logging
	logging.getLogger("uvicorn.error").warning(f"Could not create tables on startup: {e}")

app = FastAPI(title="FTTH Management System")

app.mount("/static", StaticFiles(directory="web/publica"), name="static")

# Allow cross origin requests for development. Tighten this in production.
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Basic rotating file logger (can be monitored by fail2ban if desired). Keep this optional.
os.makedirs("logs", exist_ok=True)
handler = RotatingFileHandler("logs/ftth.log", maxBytes=10 * 1024 * 1024, backupCount=5)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)
try:
	# Also add optional syslog handler for production
	syslog_handler = SysLogHandler(address="/dev/log")
	syslog_handler.setFormatter(formatter)
	root_logger.addHandler(syslog_handler)
except Exception:
	# ignore syslog errors in environments without /dev/log
	pass

# Include routers
from app.routes import works, technicians, teams, stats, auth, telegram, documents, health, manual, debug, onts, modems, sync
from telegram_endpoints import router as telegram_router
app.include_router(works.router)
app.include_router(technicians.router)
app.include_router(teams.router)
app.include_router(stats.router)
app.include_router(auth.router)
app.include_router(telegram.router)
app.include_router(telegram_router, tags=["telegram"])
app.include_router(documents.router)
app.include_router(health.router)
app.include_router(manual.router)
app.include_router(debug.router)
app.include_router(onts.router)
app.include_router(modems.router)
app.include_router(sync.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
	logging.getLogger('uvicorn.error').exception('Unhandled exception', exc_info=exc)
	return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
async def set_bot_commands_on_startup():
	# Load environment variables from .env if present
	try:
		load_dotenv()
	except Exception:
		pass
	token = os.getenv("TELEGRAM_BOT_TOKEN")
	if not token:
		logging.getLogger("uvicorn.error").info("TELEGRAM_BOT_TOKEN not set; skipping setting bot commands on startup")
		return
	bot = Bot(token=token)
	commands = [
		BotCommand("start", "Benvenuto"),
		BotCommand("help", "Mostra comandi"),
		BotCommand("miei_lavori", "I tuoi lavori"),
		BotCommand("accetta", "Accetta un lavoro"),
		BotCommand("rifiuta", "Rifiuta un lavoro"),
		BotCommand("chiudi", "Chiudi un lavoro"),
	]
	try:
		await bot.set_my_commands(commands)
		logging.getLogger("uvicorn.error").info("Telegram bot commands set on startup")
	except Exception as e:
		logging.getLogger("uvicorn.error").exception(f"Failed to set bot commands on startup: {e}")
		# Try fallback via HTTP API
		token = get_token_from_env()
		try:
			ok = await set_bot_commands_async(token, [{"command": c.command, "description": c.description} for c in commands])
			if ok:
				logging.getLogger("uvicorn.error").info("Telegram bot commands set via HTTP fallback on startup")
		except Exception as e2:
			logging.getLogger("uvicorn.error").exception(f"Failed fallback set bot commands via HTTP on startup: {e2}")

	# Optionally set a webhook if TELEGRAM_WEBHOOK_URL is provided
	webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL')
	if webhook_url:
		try:
			await bot.set_webhook(webhook_url)
			logging.getLogger('uvicorn.error').info(f"Webhook set to {webhook_url}")
		except Exception as e:
			logging.getLogger('uvicorn.error').exception(f"Failed to set webhook to {webhook_url}: {e}")


# Routes for HTML pages
@app.get("/")
async def read_root():
    return FileResponse("web/publica/index.html")

@app.get("/gestionale.html")
async def read_gestionale():
    return FileResponse("web/publica/gestionale.html")

@app.get("/dashboard.html")
async def read_dashboard():
    return FileResponse("web/publica/dashboard.html")

@app.get("/manual_entry.html")
async def read_manual_entry():
    return FileResponse("web/publica/manual_entry.html")

@app.get("/pc_alex_gestionale.html")
async def read_pc_alex_gestionale():
    return FileResponse("web/publica/pc_alex_gestionale.html")

@app.get("/db_viewer.html")
async def read_db_viewer():
    return FileResponse("web/publica/db_viewer.html")