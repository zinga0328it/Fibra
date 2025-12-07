from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback to SQLite for local development/testing
if not DATABASE_URL:
	DATABASE_URL = "sqlite:///./ftth.db"

# For SQLite URLs, enable check_same_thread to avoid multithreaded issues during tests
connect_args = {}
if DATABASE_URL.startswith("sqlite://"):
	connect_args = {"check_same_thread": False}

logging.getLogger("uvicorn.error").info(f"Using DATABASE_URL={DATABASE_URL}")
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()