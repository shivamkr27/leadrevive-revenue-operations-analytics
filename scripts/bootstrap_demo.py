"""Initialize a NEW synthetic demo; never seed or overwrite a populated database."""
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sqlalchemy import inspect,text
from backend.app.foundation import engine_for


def main():
    os.chdir(ROOT)
    if not os.environ.get('DATABASE_URL'):
        raise RuntimeError('Explicit DATABASE_URL required; no implicit SQLite fallback.')
    engine=engine_for(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        populated='leads' in inspect(conn).get_table_names() and conn.execute(text('SELECT count(*) FROM leads')).scalar()>0
    engine.dispose()
    if populated:
        print('Existing leads detected: no seeding, migrations or records changed. Review migrations separately.')
        return
    # Generator fixtures are mounted read-only in Docker, not private bootstrap history.
    if not (ROOT/'data/synthetic/leads_SYNTHETIC.csv').is_file():
        raise RuntimeError('Synthetic seed CSV missing. Generate fixtures before bootstrapping.')
    from scripts.seed_db import main as seed
    seed()


if __name__=='__main__':main()
