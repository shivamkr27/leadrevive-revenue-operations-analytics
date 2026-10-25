"""Initialize PostgreSQL once; later startups migrate schema without recopying edited data."""
import json
import os
from pathlib import Path
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sqlalchemy import select,inspect,text
from alembic import command
from alembic.config import Config
from backend.app import models as m
from backend.app.foundation import engine_for
from scripts.local_config import postgres_url
from scripts.migrate_to_postgres import main as migrate,digest


def main():
    os.chdir(ROOT)
    engine=engine_for(postgres_url())
    with engine.connect() as conn:
        names=inspect(conn).get_table_names()
        count=conn.execute(text('SELECT COUNT(*) FROM leads')).scalar() if 'leads' in names else 0
    if not count:
        engine.dispose();migrate();engine=engine_for(postgres_url())
    with engine.connect() as conn:
        marker=conn.execute(select(m.config.c.value_json).where(m.config.c.key=='sqlite_migration_verified')).scalar()
    if not marker:
        report_path=ROOT/'data/processed/postgres_migration.json'
        if not report_path.exists() or json.loads(report_path.read_text())['result']!='passed':
            raise RuntimeError('Nonempty PostgreSQL has no verified migration evidence; refusing to overwrite or silently adopt it.')
        original=engine_for('sqlite:///'+(ROOT/'data/processed/leadrevive.sqlite').as_posix())
        with original.connect() as old,engine.begin() as new:
            old_names=set(inspect(old).get_table_names())
            for table in m.metadata.sorted_tables:
                if table.name not in old_names:continue
                rows=[dict(r) for r in old.execute(select(table)).mappings()]
                pk=list(table.primary_key.columns)[0].name;ids={r[pk] for r in rows}
                current=[dict(r) for r in new.execute(select(table)).mappings() if r[pk] in ids]
                if digest(rows)!=digest(current):raise RuntimeError('Original migration rows differ: '+table.name+'; manual reconciliation required.')
            new.execute(m.config.insert().values(key='sqlite_migration_verified',value_json=json.dumps({'verified':True,'at':datetime.now(timezone.utc).isoformat(),'source':'SQLite backup preserved'})))
        original.dispose()
    previous=os.environ.get('DATABASE_URL');os.environ['DATABASE_URL']=postgres_url()
    try:command.upgrade(Config('alembic.ini'),'head')
    finally:
        if previous is None:os.environ.pop('DATABASE_URL',None)
        else:os.environ['DATABASE_URL']=previous
    engine.dispose()
    print('PostgreSQL migration verified. Existing records preserved; subsequent startups do not recopy SQLite.')


if __name__=='__main__':main()
