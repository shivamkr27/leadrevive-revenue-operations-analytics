"""Refresh the synthetic analytics pack from canonical PostgreSQL; no sends."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.local_config import postgres_url
from backend.app.foundation import engine_for
from backend.app.analytics import build_snapshot, csv_text, KPI_FIELDS


from backend.app.exporting import write_pack
from backend.app.artifacts import current_dir


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--as-of',default=datetime.now(timezone.utc).isoformat())
    parser.add_argument('--start',default='1900-01-01T00:00:00Z',help='Inclusive lead-creation cohort start (UTC ISO).')
    parser.add_argument('--end',default='2100-01-01T00:00:00Z',help='Exclusive lead-creation cohort end (UTC ISO).')
    parser.add_argument('--apply-powerbi-verification',action='store_true')
    args=parser.parse_args()
    engine=None
    if args.apply_powerbi_verification:
        snapshot=json.loads((current_dir()/'snapshot.json').read_text(encoding='utf-8'))
        proof=json.loads((ROOT/'data/processed/phase4_powerbi.json').read_text(encoding='utf-8-sig'))
        if proof['snapshot_id']!=snapshot['snapshot_id']:raise ValueError('Power BI snapshot mismatch')
        snapshot['power_bi_verification']=proof
    else:
        engine=engine_for(postgres_url())
        snapshot=build_snapshot(engine,args.as_of,args.start,args.end)
    write_pack(snapshot,ROOT/'analytics/exports')
    if engine:engine.dispose()
    print(json.dumps(dict(snapshot_id=snapshot['snapshot_id'],as_of=snapshot['as_of_utc'],kpis=snapshot['kpis'],operations=snapshot['operations']),indent=2))
