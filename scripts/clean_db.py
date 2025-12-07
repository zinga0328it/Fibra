#!/usr/bin/env python3
"""
Safe DB cleaning script for development: backs up the existing DB file (SQLite), removes it,
recreates the schema and optionally tidies up temporary test DB files in /tmp.

Usage:
  python3 scripts/clean_db.py --db sqlite:///./ftth.db --backup --force --tidy-temp

CAUTION: For non-SQL databases (postgres/mysql), this script will drop all tables and recreate schema if --force is given.
Make sure you target a development database.
"""
import os
import shutil
import argparse
import datetime
import glob
import stat
from urllib.parse import urlparse

try:
    # project modules
    from app.database import DATABASE_URL as APP_DATABASE_URL
    from app.models import models
except Exception:
    APP_DATABASE_URL = None

from sqlalchemy import create_engine


def parse_args():
    p = argparse.ArgumentParser(description='Clean a development database (SQLite/Postgres)')
    p.add_argument('--db', default=None, help='DATABASE_URL to use (default reads env or app config)')
    p.add_argument('--backup', action='store_true', help='Backup DB before deleting')
    p.add_argument('--force', action='store_true', help='Proceed without confirmation')
    p.add_argument('--tidy-temp', action='store_true', help='Remove /tmp/test_test_*.db files')
    return p.parse_args()


def backup_file(path):
    if not os.path.exists(path):
        return None
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    dst = f"{path}.bak.{ts}"
    shutil.copy2(path, dst)
    print(f"Backed up {path} -> {dst}")
    return dst


def clean_sqlite(path, backup=False, force=False):
    if not os.path.exists(path):
        print(f"SQLite DB file {path} does not exist. Creating new DB.")
    else:
        if not force:
            yn = input(f"About to delete SQLite DB {path}. Continue? [y/N]: ")
            if yn.lower() not in ('y', 'yes'):
                print('Aborted')
                return False
        if backup:
            backup_file(path)
        try:
            os.remove(path)
            print(f"Removed {path}")
        except Exception as e:
            print(f"Failed to remove {path}: {e}")
            return False

    # touch the new file and create schema
    open(path, 'a').close()
    os.chmod(path, 0o666)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    try:
        models.Base.metadata.create_all(bind=engine)
        print(f"Recreated schema in {path}")
    except Exception as e:
        print(f"Failed to recreate schema: {e}")
        return False
    return True


def clean_other_db(url, backup=False, force=False):
    # For non-sqlite, we'll drop all tables then recreate if forced
    if not force:
        yn = input(f"About to drop all tables on {url}. Continue? [y/N]: ")
        if yn.lower() not in ('y', 'yes'):
            print('Aborted')
            return False
    engine = create_engine(url)
    try:
        models.Base.metadata.drop_all(bind=engine)
        models.Base.metadata.create_all(bind=engine)
        print(f"Dropped and recreated schema on {url}")
    except Exception as e:
        print(f"Failed to drop/create on {url}: {e}")
        return False
    return True


def tidy_temp_files():
    files = glob.glob('/tmp/test_test_*.db')
    if not files:
        print('No temp test DB files found in /tmp')
        return
    print(f"Found {len(files)} files to remove")
    for f in files:
        try:
            os.remove(f)
            print(f"Removed {f}")
        except Exception as e:
            print(f"Failed to remove {f}: {e}")


def main():
    args = parse_args()
    url = args.db or os.getenv('DATABASE_URL') or APP_DATABASE_URL or 'sqlite:///./ftth.db'
    print('Target DB URL:', url)
    parsed = urlparse(url)
    backup = args.backup
    force = args.force

    if parsed.scheme == 'sqlite':
        path = url.replace('sqlite:///', '')
        if path == ':memory:':
            print('In-memory sqlite cannot be cleaned the same way; nothing to do.')
        else:
            # Ensure path is safe to remove
            abs_path = os.path.abspath(path)
            workspace_root = os.path.abspath('.')
            # allow only if in workspace or /tmp or explicitly file in current dir
            if not (abs_path.startswith(workspace_root) or abs_path.startswith('/tmp')):
                print(f"Refusing to delete DB outside workspace or /tmp: {abs_path}")
                return 1
            ok = clean_sqlite(abs_path, backup=backup, force=force)
            if not ok:
                return 1
    else:
        print('Non-sqlite DB detected. This will drop all tables (if --force).')
        if not force:
            print('Use --force to proceed with destructive operations on non-sqlite DBs.')
            return 1
        ok = clean_other_db(url, backup=backup, force=force)
        if not ok:
            return 1

    if args.tidy_temp:
        tidy_temp_files()

    print('DB clean completed')
    return 0


if __name__ == '__main__':
    exit(main() or 0)
