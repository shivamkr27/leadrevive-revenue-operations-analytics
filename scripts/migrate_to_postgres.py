"""Backup SQLite, upgrade empty/compatible Postgres, copy and reconcile all original rows."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.local_config import postgres_url
from backend.app import models as m
from backend.app.foundation import engine_for,kpis
from sqlalchemy import select,inspect,text
from alembic import command
from alembic.config import Config


def digest(rows):
    return hashlib.sha256(json.dumps(sorted(rows,key=lambda r:json.dumps(r,sort_keys=True)),sort_keys=True).encode()).hexdigest()


def transfer(source,target):
    report={}
    names=set(inspect(source).get_table_names())
    with source.connect() as old, target.begin() as new:
        for table in m.metadata.sorted_tables:
            if table.name not in names:
                continue
            rows=[dict(r) for r in old.execute(select(table)).mappings()]
            current=[dict(r) for r in new.execute(select(table)).mappings()]
            pk=list(table.primary_key.columns)[0].name
            existing={r[pk]:r for r in current}
            for row in rows:
                if row[pk] in existing:
                    if existing[row[pk]]!=row:
                        raise RuntimeError(f'{table.name}: existing target record differs; refusing overwrite')
                else:
                    new.execute(table.insert().values(**row))
            copied=[dict(r) for r in new.execute(select(table)).mappings() if r[pk] in {x[pk] for x in rows}]
            if digest(rows)!=digest(copied):
                raise RuntimeError(f'{table.name}: reconciliation mismatch')
            report[table.name]=dict(rows=len(rows),sha256=digest(rows),verified=True)
    return report


def main():
    os.chdir(ROOT)
    source_path=ROOT/'data/processed/leadrevive.sqlite'
    if not source_path.exists():
        raise RuntimeError('Existing SQLite database missing. No implicit reset or regeneration is performed.')
    backup_dir=ROOT/'data/backups'
    backup_dir.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=backup_dir/f'pre_postgres_{stamp}.sqlite'
    with sqlite3.connect(source_path) as src,sqlite3.connect(backup) as dest:
        src.backup(dest)
    target_url=postgres_url()
    engine=engine_for(target_url)
    with engine.connect() as conn:
        version=conn.execute(text('SELECT version()')).scalar().split(',')[0]
    previous=os.environ.get('DATABASE_URL')
    os.environ['DATABASE_URL']=target_url
    try:
        command.upgrade(Config(str(ROOT/'alembic.ini')),'head')
    finally:
        if previous is None:os.environ.pop('DATABASE_URL',None)
        else:os.environ['DATABASE_URL']=previous
    source=engine_for('sqlite:///'+source_path.as_posix())
    report=transfer(source,engine)
    baseline='2026-10-24T00:00:00Z'
    before,after=kpis(source,baseline),kpis(engine,baseline)
    if before!=after:
        raise RuntimeError('KPI reconciliation failed; do not switch application')
    evidence=dict(result='passed',database=version,backup=str(backup.relative_to(ROOT)),
                  tables=report,kpis_match=True,kpis=after,source_preserved=True)
    (ROOT/'data/processed/postgres_migration.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence,indent=2))
    source.dispose();engine.dispose()


if __name__=='__main__':main()
