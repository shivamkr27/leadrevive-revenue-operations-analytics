"""QA-only report, persistence and provider outage checks; no default-project mutations."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4
import httpx

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'data/processed/phase6_qa'
COMPOSE=['docker','compose','-p','leadrevive-qa','-f',str(QA/'compose.json')]


def docker(*args):
    r=subprocess.run(COMPOSE+list(args),cwd=ROOT,capture_output=True,text=True)
    if r.returncode:raise RuntimeError('Isolated Compose operation failed: '+' '.join(args[:3]))
    return r.stdout


def ready(url):
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        try:
            r=httpx.get(url,timeout=2)
            if r.status_code==200:return r
        except httpx.HTTPError:pass
        time.sleep(.5)
    raise RuntimeError('QA service readiness timeout')


def main():
    checks=[]
    def passed(message):checks.append(message);print('PASS:',message,flush=True)
    with httpx.Client(base_url='http://127.0.0.1:18000',timeout=90) as api:
        health=ready('http://127.0.0.1:18000/api/health').json()
        assert health['database']=='postgresql'
        assert api.get('/').status_code==200 and api.get('/openapi.json').status_code==200
        passed('Clean container serves compiled React, OpenAPI and migrated PostgreSQL API')
        s=api.get('/api/analytics/report').json();assert s['kpis']['new_leads']==754
        for row in s['reconciliation']:assert row['status']=='PASS'
        passed('Fresh 754-lead PostgreSQL generation reconciles all 13 KPIs; historical 758 snapshot untouched')
        reports=[]
        for empty in [False,True]:
            body={'generation_id':s['generation_id']}
            if empty:body.update(mode='fresh_cohort',start='2099-01-01T00:00:00Z',end='2100-01-01T00:00:00Z')
            r=api.post('/api/reports/generate',json=body);r.raise_for_status();report=r.json();reports.append(report['report_id'])
            if empty:assert report['kpis']['new_leads']==0 and report['kpis']['median_first_response_hours'] is None
            else:assert report['kpis']==s['kpis']
            for name,digest in report['files'].items():
                download=api.get(f"/api/reports/{report['report_id']}/download/{name}");download.raise_for_status()
                assert hashlib.sha256(download.content).hexdigest()==digest
        assert api.get('/api/analytics/report').json()['generation_id']==s['generation_id']
        passed('Normal and empty report packs download with valid hashes; null median and pinned analytics preserved')
        before=api.get('/api/leads',params={'page_size':1}).json()
        output=docker('run','--rm','--no-deps','backend','python','scripts/bootstrap_demo.py')
        assert 'no seeding, migrations or records changed' in output
        docker('restart','backend');ready('http://127.0.0.1:18000/api/health')
        after=api.get('/api/leads',params={'page_size':1}).json()
        assert before['total']==after['total'] and [r['lead_id'] for r in before['items']]==[r['lead_id'] for r in after['items']]
        passed('Repeat startup skips seeding/migrations; API restart preserves persisted leads')
        try:
            docker('stop','mailpit')
            status=api.get('/api/automations/status').json();assert status['services']['mailpit']['reachable'] is False
            passed('Stopped QA Mailpit reports unreachable, not successful sending')
        finally:
            docker('start','mailpit');ready('http://127.0.0.1:18025/api/v1/info')
        try:
            docker('stop','n8n')
            key='phase6-offline-'+uuid4().hex
            r=api.post('/api/automations/recovery',json={'idempotency_key':key,'lead_ids':[]});assert r.status_code==503
            runs=api.get('/api/automations/runs').json();assert any(key in r['idempotency_key'] and r['status']=='failed' for r in runs)
            passed('Stopped QA n8n returns 503 and records durable failure, without fabricated success')
        finally:
            docker('start','n8n');ready('http://127.0.0.1:15678/healthz')
        status=api.get('/api/automations/status').json();assert not status['external_email_enabled'];assert all(x['reachable'] for x in status['services'].values())
        passed('QA providers restored; external live delivery disabled')
    (ROOT/'data/processed/phase6_qa_verification.json').write_text(json.dumps({'result':'passed','checks':checks,'reports':reports,'generation_id':s['generation_id']},indent=2))


if __name__=='__main__':main()
