#!/usr/bin/env python3
import os, stat
DB='/tmp/test_db_write.db'
os.environ['DATABASE_URL'] = f"sqlite:///{DB}"
open(DB, 'a').close()
try:
    os.chmod(DB, 0o666)
except Exception as e:
    print('chmod failed', e)

from app.database import SessionLocal, engine
from app.models import models
print('DATABASE_URL', os.environ.get('DATABASE_URL'))
try:
    models.Base.metadata.create_all(bind=engine)
    print('Created tables ok')
except Exception as e:
    print('Create tables error', e)

try:
    db = SessionLocal()
    from app.models.models import Team
    t=Team(nome='ttest')
    db.add(t)
    db.commit()
    db.refresh(t)
    print('Created team id', t.id)
    db.close()
except Exception as e:
    print('Error while writing to DB', e)
