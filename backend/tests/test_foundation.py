import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from sqlalchemy import select, text, inspect
from sqlalchemy.engine import make_url
from uuid import uuid4
from backend.app import models as m
from backend.app.foundation import engine_for, import_csv, kpis, normalize, priority, sla_status, recovery_candidates, iso, record_event
from scripts.generate_synthetic_data import generate, write_dataset

NOW = '2026-10-24T00:00:00Z'


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.url = 'sqlite:///'+(self.root/'test.sqlite').as_posix()
        self.pg_admin=None
        if os.environ.get('LEADREVIVE_TEST_POSTGRES_URL'):
            self.pg_admin=engine_for(os.environ['LEADREVIVE_TEST_POSTGRES_URL'])
            self.pg_schema='lr_test_'+uuid4().hex
            with self.pg_admin.begin() as conn:
                conn.execute(text('CREATE SCHEMA '+self.pg_schema))
            self.url=make_url(os.environ['LEADREVIVE_TEST_POSTGRES_URL']).update_query_dict(
                {'options':'-csearch_path='+self.pg_schema}).render_as_string(hide_password=False)
        self.env = patch.dict(os.environ, {'DATABASE_URL': self.url})
        self.env.start()
        self.cfg = Config('alembic.ini')
        command.upgrade(self.cfg, 'head')
        self.engine = engine_for(self.url)
        with self.engine.begin() as conn:
            conn.execute(m.owners.insert(), [dict(owner_id=f'REP-{i}', name=f'Fictional Rep {i}', active=True) for i in range(1,5)])
        write_dataset(self.root)

    def tearDown(self):
        self.engine.dispose()
        self.env.stop()
        if self.pg_admin is not None:
            with self.pg_admin.begin() as conn:
                conn.execute(text('DROP SCHEMA '+self.pg_schema+' CASCADE'))
            self.pg_admin.dispose()
        self.tmp.cleanup()

    def ingest(self):
        return import_csv(self.engine, self.root/'leads_SYNTHETIC.csv', NOW)

    def test_import_replay_and_audits(self):
        result = self.ingest()
        self.assertEqual({k:result[k] for k in ['accepted','invalid','duplicates','review_required']},
                         dict(accepted=754, invalid=32, duplicates=7, review_required=7))
        self.assertTrue(self.ingest()['replay'])
        with self.engine.connect() as conn:
            for table, count in [('leads',754),('import_batches',1),('import_rejections',46),
                                 ('lead_activities',754),('lead_status_history',754),('audit_events',754),('lead_merge_audit',14)]:
                self.assertEqual(conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar(), count)
            if self.engine.dialect.name=='sqlite':
                self.assertEqual(conn.execute(text('PRAGMA foreign_key_check')).all(), [])
            else:
                self.assertTrue(inspect(conn).get_foreign_keys('leads'))
            self.assertEqual(len(conn.execute(select(m.leads.c.lead_id).where(m.leads.c.consent_to_email.is_(True))).all()),0)

    def test_kpi_reconciliation(self):
        self.ingest()
        result = kpis(self.engine, NOW)
        self.assertEqual((result['new_leads'],result['contacted'],result['overdue'],result['active_scheduled']), (754,572,390,586))
        self.assertEqual(result['median_first_response_hours'],59.5)
        with self.engine.connect() as conn:
            exposure = conn.execute(text('''SELECT SUM(estimated_value_paise) FROM v_open_pipeline
                WHERE next_action_at < :as_of'''), {'as_of':iso(NOW)}).scalar()/100
            self.assertEqual(exposure,result['pipeline_exposure_inr'])
            self.assertEqual(conn.execute(text('SELECT SUM(lead_count) FROM v_source_funnel')).scalar(),754)

    def test_empty_cohort_and_date_window(self):
        result = kpis(self.engine,NOW)
        self.assertIsNone(result['first_response_coverage'])
        self.assertIsNone(result['overdue_rate'])
        self.assertEqual(result['pipeline_exposure_inr'],0)
        self.ingest()
        self.assertEqual(kpis(self.engine,NOW,'2026-10-23T00:00:00Z','2026-10-24T00:00:00Z')['new_leads'],0)
        with self.assertRaises(ValueError):
            kpis(self.engine,NOW,NOW,NOW)

    def test_validation_and_default_consent(self):
        row = generate(count=1)[0]
        row.pop('consent_to_email')
        result, errors = normalize(row)
        self.assertFalse(errors)
        self.assertFalse(result['consent_to_email'])
        for field, value in [('email','bad'),('company',''),('stage','bad'),
                             ('estimated_deal_value_inr','NaN'),('created_at','2026-01-01'),
                             ('response_sla_hours','0'),('consent_to_email','maybe')]:
            bad = dict(row, **{field:value})
            self.assertTrue(normalize(bad)[1], field)
        self.assertTrue(normalize(dict(row,response_sla_hours='9999999999999999'))[1])

    def test_score_bounds_and_explanation(self):
        lead, _ = normalize(generate(count=1)[0])
        lead.update(stage='Proposal',next_action_at='2020-01-01T00:00:00Z',
                    last_contacted_at=NOW, email_verified=True)
        score = priority(lead,NOW,[lead['estimated_value_paise']-1])
        self.assertEqual(score['score'],100)
        self.assertAlmostEqual(sum(score['breakdown'].values()),100)
        lead.update(stage='New',next_action_at=None,last_contacted_at=None,email_verified=False)
        result = priority(lead,NOW,[])
        self.assertEqual(set(result['missing']),{'overdue','recency'})
        self.assertTrue(0 <= result['score'] <= 100)
        with self.assertRaises(ValueError):
            priority(lead,NOW,[], {'bad':100})

    def test_closed_leads_excluded_and_migration_reversible(self):
        self.ingest()
        with self.engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM v_open_pipeline WHERE stage IN ('Won','Lost')")).scalar(),0)
        self.engine.dispose()
        command.downgrade(self.cfg,'base')
        self.assertNotIn('leads',inspect(self.engine).get_table_names())
        command.upgrade(self.cfg,'head')
        self.assertEqual(kpis(self.engine,NOW)['new_leads'],0)

    def test_sla_elapsed_boundary(self):
        lead, _ = normalize(generate(count=1)[0])
        lead.update(created_at='2026-10-23T00:00:00Z',first_contacted_at=None,response_sla_hours=24)
        self.assertFalse(sla_status(lead,NOW)['breached'])
        self.assertTrue(sla_status(lead,'2026-10-24T00:00:01Z')['breached'])
        lead['first_contacted_at']='2026-10-23T12:00:00Z'
        self.assertFalse(sla_status(lead,NOW)['breached'])

    def test_all_overdue_all_contacted_and_recovery_filters(self):
        self.ingest()
        with self.engine.begin() as conn:
            conn.execute(m.leads.update().values(stage='Contacted',owner_id='REP-1',
                next_action_at='2026-10-23T00:00:00Z',first_contacted_at='2026-10-23T00:00:00Z'))
        snapshot = kpis(self.engine,NOW)
        self.assertEqual(snapshot['overdue_rate'],1)
        self.assertEqual(snapshot['first_response_coverage'],1)
        with self.engine.begin() as conn:
            self.assertEqual(len(recovery_candidates(conn,NOW)),754)
            conn.execute(m.leads.update().values(suppressed=True))
            self.assertEqual(len(recovery_candidates(conn,NOW)),0)
            conn.execute(m.leads.update().values(suppressed=False,owner_id=None))
            self.assertEqual(len(recovery_candidates(conn,NOW)),0)

    def test_competing_identity_candidates_preserve_existing(self):
        import csv
        self.ingest()
        with self.engine.connect() as conn:
            before = [dict(r) for r in conn.execute(select(m.leads)).mappings()]
        raw = generate(count=1)[0]
        raw.update(lead_id='SYN-CONFLICT', email=before[0]['email'].upper(),phone=before[1]['phone'])
        path = self.root/'conflict.csv'
        with path.open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(raw)); writer.writeheader(); writer.writerow(raw)
        result=import_csv(self.engine,path,NOW)
        self.assertEqual(result['review_required'],1)
        with self.engine.connect() as conn:
            after=[dict(r) for r in conn.execute(select(m.leads)).mappings()]
            self.assertEqual(before,after)
            audit=conn.execute(select(m.lead_merge_audit).where(m.lead_merge_audit.c.event_type=='review_required')).mappings().all()
            self.assertTrue(any(len(json.loads(r['details_json'])['candidate_ids'])==2 for r in audit))

    def test_qualified_history_survives_lost_stage(self):
        self.ingest()
        before=kpis(self.engine,NOW)['qualified']
        with self.engine.begin() as conn:
            lead=conn.execute(select(m.leads).where(m.leads.c.stage=='New')).mappings().first()
            conn.execute(m.leads.update().where(m.leads.c.lead_id==lead['lead_id']).values(stage='Lost'))
            record_event(conn,m.lead_status_history,lead['lead_id'],'stage_changed',{'stage':'Meeting'},iso(NOW))
        self.assertEqual(kpis(self.engine,NOW)['qualified'],before+1)

    def test_fractional_timestamp_order_and_sla_late_response(self):
        self.assertLess(iso('2026-01-01T00:00:00Z'),iso('2026-01-01T00:00:00.5Z'))
        self.assertEqual(iso('2026-01-01T05:30:00+05:30'),iso('2026-01-01T00:00:00Z'))
        lead,_=normalize(generate(count=1)[0])
        lead.update(created_at='2026-10-22T00:00:00Z',first_contacted_at='2026-10-23T00:00:01Z')
        self.assertTrue(sla_status(lead,NOW)['breached'])

    def test_exact_score_ties_and_custom_weights(self):
        lead,_=normalize(generate(count=1)[0])
        lead.update(stage='Qualified',estimated_value_paise=100,next_action_at='2026-10-20T12:00:00Z',
                    last_contacted_at='2026-10-09T00:00:00Z',email_verified=False)
        result=priority(lead,NOW,[100,100])
        self.assertEqual(result['breakdown'],dict(overdue=17.5,value=12.5,stage=10,contactability=0,recency=5))
        self.assertEqual(result['score'],45)
        for bad in [dict(overdue=-1,value=61,stage=20,contactability=10,recency=10),
                    dict(overdue=float('nan'),value=25,stage=20,contactability=10,recency=10)]:
            with self.assertRaises(ValueError): priority(lead,NOW,[],bad)

    def test_actual_export_files_reconcile(self):
        import csv
        from scripts.export_foundation import export_foundation
        self.ingest()
        export_foundation(self.engine,self.root/'exports',NOW)
        with (self.root/'exports/exceptions_SYNTHETIC.csv').open() as stream:
            self.assertEqual(len(list(csv.DictReader(stream))),46)
        with (self.root/'exports/priority_queue_SYNTHETIC.csv').open() as stream:
            queue=list(csv.DictReader(stream))
        self.assertEqual(len(queue),633)
        with self.engine.connect() as conn:
            lead=conn.execute(select(m.leads).where(m.leads.c.lead_id==queue[0]['lead_id'])).mappings().one()
            values=conn.execute(select(m.leads.c.estimated_value_paise).where(m.leads.c.stage.not_in(['Won','Lost']))).scalars().all()
        self.assertEqual(float(queue[0]['score']),priority(lead,NOW,values)['score'])
        self.assertEqual(sum(float(v) for v in json.loads(queue[0]['breakdown']).values()),
                         sum(priority(lead,NOW,values)['breakdown'].values()))

    def test_populated_legacy_migration_preserves_lead_and_normalizes_precision(self):
        self.engine.dispose()
        command.downgrade(self.cfg,'0001')
        raw,_=normalize(generate(count=1)[0])
        raw.update(created_at='2026-01-01T00:00:00Z',updated_at='2026-01-01T00:00:00.5Z',
                   first_contacted_at=None,last_contacted_at=None,next_action_at=None)
        with self.engine.begin() as conn:
            conn.execute(m.leads.insert().values(**raw))
        command.upgrade(self.cfg,'head')
        with self.engine.connect() as conn:
            saved=conn.execute(select(m.leads)).mappings().one()
            self.assertEqual(saved['created_at'],'2026-01-01T00:00:00.000000Z')
            self.assertEqual(saved['updated_at'],'2026-01-01T00:00:00.500000Z')
            self.assertEqual(saved['estimated_value_paise'],raw['estimated_value_paise'])


if __name__ == '__main__':
    unittest.main()
