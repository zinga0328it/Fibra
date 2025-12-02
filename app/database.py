from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Provide a fallback to SQLite for local development/testing when DATABASE_URL isn't set
if not DATABASE_URL:
	DATABASE_URL = "sqlite:///./ftth.db"
	engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
	engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()