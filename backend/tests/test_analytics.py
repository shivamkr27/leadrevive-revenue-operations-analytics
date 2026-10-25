import csv
import io
import os
import unittest
from unittest.mock import patch
import json
from fastapi.testclient import TestClient
from sqlalchemy import text
from backend.tests import test_foundation as ft
from backend.app.analytics import build_snapshot, sql_kpis, experiment, csv_text, KPI_FIELDS
from backend.app.foundation import kpis
from scripts.build_phase4 import write_pack
from backend.app.artifacts import current_dir


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        ft.FoundationTests.setUp(self)

    def tearDown(self):
        ft.FoundationTests.tearDown(self)

    def test_view_and_csv_formula_safety(self):
        ft.FoundationTests.ingest(self)
        with self.engine.connect() as conn:
            self.assertEqual(conn.execute(text('SELECT COUNT(*) FROM v_analytics_leads')).scalar(),754)
        parsed=list(csv.DictReader(io.StringIO(csv_text([dict(label='=2+2',origin='SYNTHETIC')]))))
        self.assertEqual(parsed[0]['label'],"'=2+2")

    def test_simulation_comparable_events_and_explicit_assumptions(self):
        a,b=experiment(),experiment()
        self.assertEqual(a['rows'],b['rows'])
        self.assertEqual(len(a['rows']),40)
        self.assertEqual(a['summary'][0]['cohort'],a['summary'][1]['cohort'])
        self.assertTrue(all(r['automation_action_hour']<=r['manual_action_hour'] for r in a['rows']))
        self.assertIn('assumed',a['summary'][0]['timing_basis'])
        self.assertGreater(a['summary'][0]['followups_completed'],0)
        self.assertGreater(a['summary'][1]['followups_completed'],a['summary'][0]['followups_completed'])

    def test_snapshot_routes_require_build_and_hide_row_facts(self):
        from backend.app.api import create_app
        directory=self.root/'exports';directory.mkdir()
        app=create_app(self.url,fixed_now=ft.NOW)
        try:
            with patch('backend.app.analytics_api.EXPORTS',directory),TestClient(app) as client:
                self.assertEqual(client.get('/api/analytics/report').status_code,503)
                (directory/'snapshot.json').write_text(json.dumps(dict(snapshot_id='unit',origin='SYNTHETIC',facts=[{'lead_id':'hidden'}])))
                (directory/'manifest.json').write_text(json.dumps(dict(snapshot_id='unit',files={})))
                report=client.get('/api/analytics/report').json()
                self.assertNotIn('facts',report)
                self.assertEqual(report['origin'],'SYNTHETIC')
                (directory/'KPI_SYNTHETIC.csv').write_text('metric,value\nnew_leads,0\n')
                self.assertEqual(client.get('/api/analytics/export/KPI_SYNTHETIC.csv').status_code,200)
                self.assertEqual(client.get('/api/analytics/export/snapshot.json').status_code,404)
                self.assertEqual(client.get('/api/analytics/export/.env').status_code,404)
        finally:app.state.engine.dispose()

    @unittest.skipUnless(os.environ.get('LEADREVIVE_TEST_POSTGRES_URL'),'PostgreSQL independent SQL only')
    def test_postgres_snapshot_excel_csv_reconcile_and_empty_cohort(self):
        ft.FoundationTests.ingest(self)
        result=build_snapshot(self.engine,ft.NOW)
        self.assertEqual(result['kpis']['new_leads'],754)
        self.assertEqual(sum(r['sla_met']+r['sla_breached']+r['awaiting_within_sla'] for r in result['facts']),754)
        self.assertEqual(sum(r['cohort_kind']=='Seed dataset' for r in result['facts']),754)
        exported=write_pack(result,self.root/'exports')
        rows=list(csv.DictReader((exported/'LeadFacts_SYNTHETIC.csv').open(encoding='utf-8-sig',newline='')))
        self.assertEqual(len(rows),754)
        self.assertEqual(sum(float(r['pipeline_exposure_inr']) for r in rows),result['sql_kpis']['pipeline_exposure_inr'])
        self.assertEqual(sum(int(r['overdue']) for r in rows),390)
        for source in ['Web','Referral','Event','InboundEmail','Manual','DOES_NOT_EXIST']:
            with self.engine.connect() as conn:
                sql=sql_kpis(conn,ft.NOW,source=source)
            app=kpis(self.engine,ft.NOW,source=source)
            for key in KPI_FIELDS:
                self.assertEqual(app[key],sql[key],(source,key))
        empty=build_snapshot(self.engine,ft.NOW,start='2099-01-01T00:00:00Z')
        self.assertEqual(empty['facts'],[])
        self.assertIsNone(empty['sql_kpis']['overdue_rate'])
