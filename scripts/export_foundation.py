"""Export synthetic SQL data-quality evidence and explained priority queue."""
import csv
import json
import os
import sys
from pathlib import Path
from sqlalchemy import select, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app import models as m
from backend.app.foundation import engine_for, priority
from backend.app.operations import settings


def export_foundation(engine, destination, as_of):
    destination = Path(destination)
    destination.mkdir(parents=True,exist_ok=True)
    with engine.connect() as conn:
        rows = conn.execute(select(m.leads)).mappings().all()
        values = [r['estimated_value_paise'] for r in rows if r['stage'] not in ['Won','Lost']]
        queue = []
        weights = settings(conn)['scoring_weights']
        for row in rows:
            if row['stage'] in ['Won','Lost']:
                continue
            score = priority(row,as_of,values,weights)
            queue.append(dict(lead_id=row['lead_id'],origin='SYNTHETIC',owner_id=row['owner_id'],
                next_action_at=row['next_action_at'],score=score['score'],
                breakdown=json.dumps(score['breakdown']),missing=json.dumps(score['missing'])))
        queue.sort(key=lambda r:(-r['score'],r['lead_id']))
        exceptions = [dict(r) for r in conn.execute(select(m.import_rejections)).mappings()]
        funnel = [dict(r) for r in conn.execute(text('SELECT * FROM v_source_funnel')).mappings()]
        for name, data in [('priority_queue_SYNTHETIC',queue),('exceptions_SYNTHETIC',exceptions),('source_funnel_SYNTHETIC',funnel)]:
            if data:
                with (destination/(name+'.csv')).open('w',encoding='utf-8',newline='') as stream:
                    writer=csv.DictWriter(stream,fieldnames=list(data[0]))
                    writer.writeheader()
                    writer.writerows(data)
            print(f'{name}: {len(data)} rows')


if __name__ == '__main__':
    engine = engine_for(os.environ.get('DATABASE_URL','sqlite:///data/processed/leadrevive.sqlite'))
    export_foundation(engine, ROOT/'data/processed', '2026-10-24T00:00:00Z')
    engine.dispose()
