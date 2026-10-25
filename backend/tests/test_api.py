import csv
import io
import json
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import select
import backend.tests.test_foundation as foundation_tests
from backend.app.api import create_app
from backend.app import models as m

NOW='2026-10-24T12:00:00Z'


class ApiTests(unittest.TestCase):
    def setUp(self):
        foundation_tests.FoundationTests.setUp(self)
        foundation_tests.FoundationTests.ingest(self)
        self.app=create_app(self.url,fixed_now=NOW)
        self.client=TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.state.engine.dispose()
        foundation_tests.FoundationTests.tearDown(self)

    def test_metrics_filtering_export_and_pagination(self):
        self.assertEqual(self.client.get('/api/health').json()['migration'],'0005')
        overview=self.client.get('/api/overview').json()
        self.assertEqual(overview['kpis']['new_leads'],754)
        self.assertEqual(sum(s['count'] for s in overview['stages']),754)
        queue=self.client.get('/api/leads',params={'followup':'overdue','owner':'REP-1','page_size':5}).json()
        self.assertLessEqual(len(queue['items']),5)
        self.assertTrue(all(r['overdue'] and r['owner_id']=='REP-1' for r in queue['items']))
        self.assertEqual(self.client.get('/api/leads?page=0').status_code,422)
        snapshot=self.client.get('/api/analytics/kpis?source=Web').json()
        exported=list(csv.DictReader(io.StringIO(self.client.get('/api/leads/export').text)))
        self.assertEqual(len(exported),754)
        self.assertEqual(snapshot['new_leads'],self.client.get('/api/leads?source=Web&open_only=false').json()['total'])
        self.assertTrue(all(r['origin']=='SYNTHETIC' for r in exported))

    def test_edits_persist_with_audit_and_reject_stale_version(self):
        row=self.client.get('/api/leads?followup=overdue').json()['items'][0]
        url='/api/leads/'+row['lead_id']
        updated=self.client.patch(url,json=dict(version=row['version'],owner_id='REP-2',stage='Qualified',next_action_at='2026-10-25T12:00:00+05:30'))
        self.assertEqual(updated.status_code,200,updated.text)
        self.assertEqual(self.client.patch(url,json=dict(version=row['version'],owner_id='REP-3')).status_code,409)
        detail=self.client.get(url).json()
        self.assertEqual(detail['owner_id'],'REP-2')
        self.assertFalse(detail['overdue'])
        self.assertTrue(any(e['category']=='audit_events' and e['details'].get('before') for e in detail['timeline']))
        self.assertEqual(self.client.patch(url,json=dict(version=detail['version'],owner_id='INVALID')).status_code,422)

    def test_contact_first_response_preserved_and_closed_guard(self):
        row=self.client.get('/api/leads?stage=New').json()['items'][0]
        url='/api/leads/'+row['lead_id']
        for index in range(2):
            row=self.client.get(url).json()
            response=self.client.post(url+'/activity',json=dict(version=row['version'],kind='contacted',note='Synthetic contact recorded'))
            self.assertEqual(response.status_code,200,response.text)
        detail=self.client.get(url).json()
        self.assertEqual(detail['stage'],'Contacted')
        first=detail['first_contacted_at']
        self.assertEqual(detail['last_contacted_at'],first)
        self.client.patch(url,json=dict(version=detail['version'],stage='Won'))
        detail=self.client.get(url).json()
        self.assertEqual(self.client.post(url+'/activity',json=dict(version=detail['version'],kind='contacted',note='No contact')).status_code,422)
        self.assertEqual(detail['first_contacted_at'],first)

    def test_conflict_review_is_audited_without_merge(self):
        quality=self.client.get('/api/quality').json()
        item=next(r for r in quality['items'] if 'collision' in r['reason'])
        before=self.client.get('/api/leads/export').text
        body=dict(decision='keep_existing',note='Conflicting fictional identity. Preserve original.')
        response=self.client.post('/api/quality/'+item['rejection_id']+'/review',json=body)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(self.client.post('/api/quality/'+item['rejection_id']+'/review',json=body).status_code,409)
        self.assertEqual(before,self.client.get('/api/leads/export').text)
        self.assertEqual(self.client.get('/api/quality?status=reviewed').json()['items'][0]['review']['note'],body['note'])
        self.assertEqual(self.client.get('/api/quality?status=pending').json()['pending'],45)
        self.assertTrue(any(r['event_type']=='exception_reviewed' for r in self.client.get('/api/audit').json()))

    def test_csv_upload_replay_and_validation(self):
        response=self.client.post('/api/leads/import',files={'file':('fixture.csv',(self.root/'leads_SYNTHETIC.csv').read_bytes(),'text/csv')})
        self.assertTrue(response.json()['replay'])
        self.assertEqual(self.client.post('/api/leads/import',files={'file':('bad.csv',b'bad,header\nx,y','text/csv')}).status_code,422)
        self.assertEqual(self.client.post('/api/leads/import',files={'file':('huge.csv',b'x'*2_000_001,'text/csv')}).status_code,413)

    def test_settings_validation_persistence_and_safe_flags(self):
        before=self.client.get('/api/settings').json()
        payload=dict(version=before['version'],response_sla_hours=12,scoring_weights=dict(overdue=100,value=0,stage=0,contactability=0,recency=0))
        response=self.client.put('/api/settings',json=payload)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(self.client.get('/api/settings').json()['response_sla_hours'],12)
        self.assertEqual(self.client.put('/api/settings',json=payload).status_code,409)
        payload['version']=2;payload['scoring_weights']['overdue']=99
        self.assertEqual(self.client.put('/api/settings',json=payload).status_code,422)
        payload['scoring_weights']['overdue']=100;payload['live_email_enabled']=True
        self.assertEqual(self.client.put('/api/settings',json=payload).status_code,422)
        self.assertFalse(response.json()['live_email_enabled'])

    def test_manual_create_and_duplicate_and_email_safety(self):
        payload=dict(full_name='Fictional API Contact',company='Synthetic API Business',email='api@business.example',
                     phone='FICTIONAL-IN-API-001',estimated_deal_value_inr='12345.67',owner_id='REP-1')
        response=self.client.post('/api/leads',json=payload)
        self.assertEqual(response.status_code,201,response.text)
        self.assertEqual(response.json()['estimated_value_paise'],1234567)
        self.assertFalse(response.json()['consent_to_email'])
        self.assertEqual(self.client.post('/api/leads',json=payload).status_code,409)
        payload['email']='person@real-company.com';payload['phone']='FICTIONAL-IN-API-002'
        self.assertEqual(self.client.post('/api/leads',json=payload).status_code,422)
        self.assertEqual(self.client.post('/api/email-drafts/test/send',json=dict(idempotency_key='missing-draft',mode='mailpit')).status_code,404)
        self.assertEqual(self.client.post('/api/email-drafts/test/send',json=dict(idempotency_key='live-blocked',mode='live')).status_code,422)

    def test_local_origin_and_missing_lead(self):
        self.assertEqual(self.client.get('/api/leads/missing').status_code,404)
        self.assertEqual(self.client.get('/api/settings',headers={'Origin':'https://external.example'}).status_code,403)

    def test_discard_invalid_and_reject_wrong_review_decision(self):
        item=next(r for r in self.client.get('/api/quality').json()['items'] if 'invalid format' in r['reason'])
        url='/api/quality/'+item['rejection_id']+'/review'
        self.assertEqual(self.client.post(url,json=dict(decision='keep_existing',note='Invalid contact')).status_code,422)
        self.assertEqual(self.client.post(url,json=dict(decision='discard_invalid',note='Invalid contact')).status_code,200)
        self.assertEqual(self.client.get('/api/analytics/kpis').json()['new_leads'],754)

    def test_first_contact_preserved_across_later_contacts(self):
        from backend.app.operations import add_activity
        from backend.app.foundation import iso
        row=self.client.get('/api/leads?stage=New').json()['items'][0]
        with self.engine.begin() as conn:
            first=add_activity(conn,row['lead_id'],row['version'],'contacted','First contact',iso(NOW))
            later=add_activity(conn,row['lead_id'],first['version'],'contacted','Later contact',iso('2026-10-24T13:00:00Z'))
        self.assertEqual(later['first_contacted_at'],iso(NOW))
        self.assertEqual(later['last_contacted_at'],iso('2026-10-24T13:00:00Z'))

    def test_unmigrated_database_reports_unavailable(self):
        other=create_app('sqlite:///'+(self.root/'empty.sqlite').as_posix())
        with TestClient(other) as client:
            response=client.get('/api/health')
            self.assertEqual(response.status_code,503)
            self.assertIn('migrations pending',response.json()['detail'])
