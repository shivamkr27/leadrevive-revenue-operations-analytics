import unittest
import os
from sqlalchemy import select
import backend.tests.test_foundation as fixtures
from backend.app import models as m
from backend.app.foundation import iso
from backend.app.automation import Automations,SinkUnavailable,UncertainAcceptance
from backend.app.operations import add_activity,edit_lead,OperationError

NOW='2026-10-24T12:00:00Z'


class FakeSink:
    """Deterministic unit transport; real SMTP/n8n paths have separate Docker tests."""
    def __init__(self):self.messages={};self.calls=0;self.fail=False;self.lose_ack=False
    def lookup(self,message_id):return self.messages.get(message_id)
    def send(self,draft,message_id):
        self.calls+=1
        if self.fail:raise SinkUnavailable('Test SMTP unavailable before DATA')
        self.messages[message_id]='sink-'+str(len(self.messages)+1)
        if self.lose_ack:raise UncertainAcceptance('Test lost SMTP acknowledgement')


class AutomationTests(unittest.TestCase):
    def setUp(self):
        fixtures.FoundationTests.setUp(self)
        fixtures.FoundationTests.ingest(self)
        self.sink=FakeSink();self.service=Automations(self.engine,self.sink)
        with self.engine.connect() as conn:
            self.lead=dict(conn.execute(select(m.leads).where(m.leads.c.stage=='New',m.leads.c.owner_id.is_not(None),m.leads.c.next_action_at<iso(NOW))).mappings().first())
    def tearDown(self):fixtures.FoundationTests.tearDown(self)

    def scan(self,key='scan',at=NOW):return self.service.recovery(key,at,lead_ids=[self.lead['lead_id']])

    def test_overdue_transition_and_grouped_cooldown_and_replay(self):
        with self.engine.begin() as conn:
            conn.execute(m.leads.update().where(m.leads.c.lead_id==self.lead['lead_id']).values(next_action_at=iso('2026-10-24T13:00:00Z')))
        self.assertEqual(self.scan('before')['processed'],0)
        due=self.scan('after','2026-10-24T13:00:01Z')
        self.assertEqual(due['processed'],1)
        self.assertEqual(self.scan('again','2026-10-24T13:00:02Z')['processed'],0)
        self.assertTrue(self.scan('after','2026-10-24T13:00:01Z')['replay'])
        delivery=self.service.dispatch('deliver','2026-10-24T13:00:03Z',draft_ids=due['draft_ids'])
        self.assertEqual(delivery['processed'],1)
        self.assertEqual(self.scan('cooldown','2026-10-24T14:00:00Z')['processed'],0)
        self.assertEqual(self.scan('expired','2026-10-25T13:00:04Z')['processed'],1)

    def test_followup_completion_cancels_reserved_reminder(self):
        result=self.scan()
        with self.engine.begin() as conn:
            add_activity(conn,self.lead['lead_id'],self.lead['version'],'contacted','Synthetic follow-up completed',iso(NOW))
        dispatch=self.service.dispatch('after-contact',NOW,draft_ids=result['draft_ids'])
        self.assertEqual(dispatch['processed'],0)
        self.assertEqual(self.sink.calls,0)
        self.assertEqual(self.scan('after-completion')['processed'],0)
        with self.engine.connect() as conn:
            self.assertEqual(conn.execute(select(m.reminder_items.c.status)).scalar(),'cancelled')

    def test_owner_reassignment_or_closed_status_cancels_pending(self):
        result=self.scan()
        changes=dict(stage='Won')
        synced=self.service.sync('close',self.lead['lead_id'],self.lead['version'],changes,NOW)
        self.assertEqual(synced['stage'],'Won')
        self.assertEqual(self.service.dispatch('closed',NOW,draft_ids=result['draft_ids'])['processed'],0)
        self.assertEqual(self.sink.calls,0)
        self.assertEqual(self.scan('no-closed')['processed'],0)

    def test_smtp_failure_and_safe_bounded_retry(self):
        result=self.scan();self.sink.fail=True
        failed=self.service.dispatch('dispatch',NOW,draft_ids=result['draft_ids'],force_retry=True)
        self.assertEqual(failed['status'],'failed')
        self.sink.fail=False
        retried=self.service.dispatch('dispatch',NOW,draft_ids=result['draft_ids'],force_retry=True)
        self.assertEqual(retried['status'],'succeeded')
        self.assertEqual(retried['attempts'],2)
        calls=self.sink.calls
        self.assertTrue(self.service.dispatch('dispatch',NOW,draft_ids=result['draft_ids'],force_retry=True)['replay'])
        self.service.dispatch('new-key',NOW,draft_ids=result['draft_ids'],force_retry=True)
        self.assertEqual(self.sink.calls,calls)
        self.assertEqual(len(self.sink.messages),1)

    def test_uncertain_ack_is_reconciled_without_second_send(self):
        result=self.scan();self.sink.lose_ack=True
        self.assertEqual(self.service.dispatch('ack',NOW,draft_ids=result['draft_ids'],force_retry=True)['failed'],1)
        self.sink.lose_ack=False
        self.assertEqual(self.service.dispatch('ack',NOW,draft_ids=result['draft_ids'],force_retry=True)['processed'],1)
        self.assertEqual(self.sink.calls,1)

    def test_three_failed_attempts_exhaust_delivery(self):
        result=self.scan();self.sink.fail=True
        for index in range(4):
            self.service.dispatch('try-'+str(index),NOW,draft_ids=result['draft_ids'],force_retry=True)
        self.assertEqual(self.sink.calls,3)

    def test_explicit_approval_and_synthetic_preview_policy(self):
        draft=self.service.preview(self.lead['lead_id'],NOW)
        result=self.service.dispatch('without-approval',NOW,draft_ids=[draft['draft_id']])
        self.assertEqual(result['processed'],0);self.assertEqual(self.sink.calls,0)
        self.assertFalse(self.lead['consent_to_email'])
        self.service.approve(draft['draft_id'],draft['version'],NOW)
        self.assertEqual(self.service.dispatch('approved',NOW,draft_ids=[draft['draft_id']])['processed'],1)
        self.assertEqual(len(self.sink.messages),1)
        with self.engine.connect() as conn:
            self.assertEqual(conn.execute(select(m.notification_approvals.c.mode)).scalar(),'mailpit_only')

    def test_lead_edit_invalidates_approval(self):
        draft=self.service.preview(self.lead['lead_id'],NOW)
        self.service.approve(draft['draft_id'],draft['version'],NOW)
        with self.engine.begin() as conn:
            edit_lead(conn,self.lead['lead_id'],self.lead['version'],{'stage':'Qualified'},iso(NOW))
        result=self.service.dispatch('stale',NOW,draft_ids=[draft['draft_id']])
        self.assertEqual(result['processed'],0);self.assertEqual(self.sink.calls,0)

    def test_intake_idempotent_assignment_and_rejected_input_visible(self):
        lead=dict(full_name='Fictional Workflow Contact',company='Synthetic Workflow Business',email='workflow@business.example',
            phone='FICTIONAL-IN-WORKFLOW-001',estimated_deal_value_inr='25000')
        first=self.service.intake('intake',lead,NOW)
        self.assertEqual(first['processed'],1)
        self.assertTrue(self.service.intake('intake',lead,NOW)['replay'])
        second=self.service.intake('other-key',lead,NOW)
        self.assertEqual(second['status'],'failed')
        self.assertTrue(self.service.intake('other-key',lead,NOW)['replay'])
        with self.engine.connect() as conn:
            self.assertEqual(conn.execute(select(m.leads.c.owner_id).where(m.leads.c.lead_id==first['lead_id'])).scalar(),'REP-1')
            self.assertEqual(len(conn.execute(select(m.notification_drafts)).all()),1)
            self.assertEqual(len(conn.execute(select(m.import_rejections).where(m.import_rejections.c.row_number==1)).all()),1)

    def test_changed_payload_reusing_key_rejected(self):
        self.scan('same-key')
        with self.assertRaises(OperationError):
            self.service.recovery('same-key',NOW,lead_ids=[])

    def test_owner_digest_groups_multiple_leads_and_honors_filters(self):
        with self.engine.connect() as conn:
            leads=conn.execute(select(m.leads).where(m.leads.c.stage=='New',m.leads.c.owner_id=='REP-1',m.leads.c.next_action_at<iso(NOW)).limit(2)).mappings().all()
        result=self.service.recovery('group',NOW,lead_ids=[r['lead_id'] for r in leads])
        self.assertEqual(result['processed'],2)
        self.assertEqual(result['digests'],1)
        self.assertEqual(len(result['draft_ids']),1)

    @unittest.skipUnless(os.environ.get('LEADREVIVE_TEST_POSTGRES_URL'),'PostgreSQL-only concurrent transaction test')
    def test_concurrent_scans_reserve_only_one_reminder(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda key:self.scan(key),['parallel-1','parallel-2']))
        self.assertEqual(sum(r['processed'] for r in results),1)
        with self.engine.connect() as conn:
            self.assertEqual(len(conn.execute(select(m.reminder_items)).all()),1)

    def test_operator_cancellation_preserves_ledger_and_stops_send(self):
        draft=self.service.preview(self.lead['lead_id'],NOW)
        self.service.approve(draft['draft_id'],draft['version'],NOW)
        self.service.cancel(draft['draft_id'],'Synthetic preview no longer needed',NOW)
        self.assertEqual(self.service.dispatch('cancelled',NOW,draft_ids=[draft['draft_id']])['processed'],0)
        self.assertEqual(self.sink.calls,0)
        with self.engine.connect() as conn:
            self.assertEqual(len(conn.execute(select(m.notification_approvals)).all()),1)
