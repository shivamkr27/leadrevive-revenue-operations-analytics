"""Publish a fresh PostgreSQL analytics generation; no email or operational writes."""
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.app.foundation import engine_for
from backend.app.analytics import build_snapshot
from backend.app.exporting import write_pack

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--as-of',default=datetime.now(timezone.utc).isoformat());args=parser.parse_args()
    if not os.environ.get('DATABASE_URL'):raise RuntimeError('Explicit DATABASE_URL required')
    engine=engine_for(os.environ['DATABASE_URL'])
    try:
        s=build_snapshot(engine,args.as_of);directory=write_pack(s,ROOT/'analytics/exports')
        print(f"Published {directory.name}: {s['kpis']['new_leads']} synthetic leads. Desktop DAX verification is pending for this NEW generation.")
    finally:engine.dispose()
