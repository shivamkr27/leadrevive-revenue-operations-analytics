"""Run comparable modeled owner actions through real application rules.

Uses disposable SQLite databases, not canonical business records; no SMTP/n8n
transport is called. Timing measures local rule execution, not human effort.
"""
import json
import sys
import tempfile
import time
from contextlib import ExitStack
from datetime import datetime,timezone,timedelta
from pathlib import Path
from sqlalchemy import select

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app import models as m
from backend.app.analytics import experiment
from backend.app.foundation import normalize,engine_for,iso,kpis
from backend.app.operations import add_activity
from backend.app.automation import Automations
from scripts.generate_synthetic_data import generate
from scripts.build_phase4 import write_pack
from backend.app.artifacts import current_dir


def run():
    modeled=experiment()
    origin=datetime(2026,10,24,tzinfo=timezone.utc)
    verified=[]
    with tempfile.TemporaryDirectory(prefix='leadrevive_experiment_') as temp, ExitStack() as cleanup:
        for arm in ['manual','automation']:
            engine=engine_for('sqlite:///'+(Path(temp)/(arm+'.sqlite')).as_posix())
            cleanup.callback(engine.dispose)
            m.metadata.create_all(engine)
            with engine.begin() as conn:
                conn.execute(m.owners.insert(),[dict(owner_id=f'REP-{i}',name=f'Fictional Rep {i}',active=True) for i in range(1,5)])
                for event,template in zip(modeled['rows'],generate(count=40)):
                    raw=dict(template,lead_id=event['lead_id'],stage='New',company='Synthetic comparison '+event['lead_id'],
                        email=event['lead_id'].lower()+'@leadrevive.example',
                        created_at=iso((origin-timedelta(days=1)).isoformat()),
                        updated_at=iso((origin-timedelta(days=1)).isoformat()),owner_id=event['owner'],
                        next_action_at=iso((origin+timedelta(hours=event['due_hour'])).isoformat()),
                        estimated_deal_value_inr='100000',last_contacted_at='',first_contacted_at='',lost_reason='')
                    normalized,errors=normalize(raw)
                    assert not errors,errors
                    conn.execute(m.leads.insert().values(**normalized))
            automation=Automations(engine)
            began=time.perf_counter();processed=0;replays=0
            for hour in range(1,25):
                at=iso((origin+timedelta(hours=hour)).isoformat())
                with engine.begin() as conn:
                    for event in modeled['rows']:
                        if event[arm+'_action_hour']==hour:
                            lead=conn.execute(select(m.leads).where(m.leads.c.lead_id==event['lead_id'])).mappings().one()
                            add_activity(conn,lead['lead_id'],lead['version'],'contacted','SYNTHETIC: modeled two-hour owner response.',at)
                if arm=='automation':
                    key=f'simulation-hour-{hour}'
                    result=automation.recovery(key,at)
                    processed+=result['processed']
                    assert automation.recovery(key,at)['replay']
                    replays+=1
            duration=(time.perf_counter()-began)*1000
            stats=kpis(engine,iso((origin+timedelta(hours=24)).isoformat()))
            expected=next(r for r in modeled['summary'] if r['arm']==arm)
            assert stats['contacted']==expected['followups_completed']
            # Raw overdue includes completed actions until rescheduled. Use action
            # completion to compare remaining work, never relabel raw KPI as cleared.
            verified.append(dict(arm=arm,followups_completed=stats['contacted'],
                incomplete_due_work=40-stats['contacted'],raw_overdue_kpi=stats['overdue'],
                reminders_reserved=processed,idempotent_hour_replays=replays,
                measured_rule_execution_ms=round(duration,3),
                outcome_basis='Owner actions modeled; application rule outcomes executed in disposable SQLite'))
            engine.dispose()
    modeled['engine_verification']=verified
    target=ROOT/'analytics/exports'
    snapshot=json.loads((current_dir(target)/'snapshot.json').read_text())
    snapshot.pop('power_bi_verification',None)
    snapshot['experiment']=modeled
    write_pack(snapshot,target)
    print(json.dumps(verified,indent=2))


if __name__=='__main__':run()
