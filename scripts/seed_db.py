"""Migrate, seed fictional reps and import synthetic fixtures; safe to repeat."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from backend.app import models as m
from backend.app.foundation import engine_for, import_csv, kpis, WEIGHTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', default='2026-10-24T00:00:00Z')
    parser.add_argument('--export-dir',type=Path,default=ROOT/'data/processed')
    args = parser.parse_args()
    os.chdir(ROOT)
    (ROOT/'data/processed').mkdir(parents=True, exist_ok=True)
    command.upgrade(Config(str(ROOT/'alembic.ini')), 'head')
    engine = engine_for(os.environ.get('DATABASE_URL', 'sqlite:///data/processed/leadrevive.sqlite'))
    with engine.begin() as conn:
        for key, value in dict(response_sla_hours=24, scoring_weights=WEIGHTS,
                               reminder_cooldown_hours=24, dry_run=True, live_email_enabled=False).items():
            if not conn.execute(select(m.config).where(m.config.c.key == key)).first():
                conn.execute(m.config.insert().values(key=key,value_json=json.dumps(value)))
        for i in range(1, 5):
            owner = f'REP-{i}'
            if not conn.execute(select(m.owners).where(m.owners.c.owner_id == owner)).first():
                conn.execute(m.owners.insert().values(owner_id=owner, name=f'Fictional Rep {i}', active=True))
    summary = import_csv(engine, ROOT/'data/synthetic/leads_SYNTHETIC.csv', args.as_of)
    snapshot = kpis(engine, args.as_of)
    args.export_dir.mkdir(parents=True,exist_ok=True)
    (args.export_dir/'kpi_snapshot.json').write_text(json.dumps(snapshot, indent=2)+'\n')
    print(json.dumps(dict(import_result=summary, kpis=snapshot), indent=2))
    engine.dispose()


if __name__ == '__main__':
    main()
