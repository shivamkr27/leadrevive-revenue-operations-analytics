import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
import backend.tests.test_foundation as fixtures
from backend.app.api import create_app
from backend.app.automation import MailpitTransport


class AutomationApiTests(unittest.TestCase):
    def setUp(self):
        fixtures.FoundationTests.setUp(self)
        fixtures.FoundationTests.ingest(self)
        self.security=patch.dict('os.environ',{'LEADREVIVE_WEBHOOK_SECRET':'unit-test-secret-not-a-real-credential'})
        self.security.start()
        self.app=create_app(self.url,fixed_now='2026-10-24T12:00:00Z')
        self.client=TestClient(self.app)
        self.headers={'X-LeadRevive-Key':'unit-test-secret-not-a-real-credential'}
    def tearDown(self):
        self.client.close();self.app.state.engine.dispose();self.security.stop()
        fixtures.FoundationTests.tearDown(self)

    def test_signed_routes_reject_missing_or_wrong_header(self):
        body=dict(idempotency_key='auth',lead_ids=[])
        self.assertEqual(self.client.post('/api/integrations/n8n/recovery',json=body).status_code,401)
        self.assertEqual(self.client.post('/api/integrations/n8n/recovery',json=body,headers={'X-LeadRevive-Key':'wrong'}).status_code,401)
        response=self.client.post('/api/integrations/n8n/recovery',json=body,headers=self.headers)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['status'],'succeeded')

    def test_preview_approval_explicit_and_live_send_always_blocked(self):
        lead=self.client.get('/api/leads?stage=New').json()['items'][0]
        draft=self.client.post('/api/leads/'+lead['lead_id']+'/email-draft').json()
        self.assertEqual(draft['status'],'pending_approval')
        self.assertEqual(self.client.post('/api/email-drafts/'+draft['draft_id']+'/send',json={'idempotency_key':'not-approved','mode':'mailpit'}).status_code,409)
        url='/api/email-drafts/'+draft['draft_id']+'/approve'
        self.assertEqual(self.client.post(url,json={'version':1,'sink_only':False}).status_code,422)
        self.assertEqual(self.client.post(url,json={'version':1,'sink_only':True}).status_code,200)
        self.assertEqual(self.client.post(url,json={'version':1,'sink_only':True}).status_code,409)
        self.assertEqual(self.client.post('/api/email-drafts/'+draft['draft_id']+'/send',json={'idempotency_key':'external-block','mode':'live'}).status_code,422)
        notification=self.client.get('/api/notifications').json()[0]
        self.assertGreaterEqual(len(notification['live_block_reasons']),4)
        self.assertEqual(notification['sink_recipient'],'approved-preview@leadrevive.test')

    def test_only_local_sink_transport_can_be_configured(self):
        with patch.dict('os.environ',{'MAILPIT_SMTP_HOST':'smtp.real-provider.example'}):
            with self.assertRaises(RuntimeError):MailpitTransport()

    def test_bad_webhook_is_visible_and_replay_does_not_repeat_rejection(self):
        body=dict(idempotency_key='invalid-intake',lead={'full_name':'Incomplete synthetic enquiry'})
        first=self.client.post('/api/integrations/n8n/intake',json=body,headers=self.headers)
        self.assertEqual(first.json()['status'],'failed')
        self.assertNotIn('error',first.json())
        self.assertIn('failure_reason',first.json())
        again=self.client.post('/api/integrations/n8n/intake',json=body,headers=self.headers)
        self.assertTrue(again.json()['replay'])
        quality=self.client.get('/api/quality').json()
        self.assertEqual(quality['total'],47)
        self.assertEqual(self.client.get('/api/analytics/kpis').json()['new_leads'],754)
