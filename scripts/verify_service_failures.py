"""Real local provider outages: correct offline status and durable n8n trigger failure."""
from pathlib import Path
import json
import subprocess
import sys
import time
from uuid import uuid4
import httpx

ROOT=Path(__file__).resolve().parents[1]


def main():
    evidence={'result':'running','checks':[]}
    def docker(*args):subprocess.run(['docker','compose',*args],cwd=ROOT,check=True,capture_output=True)
    def ready(url):
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            try:
                if httpx.get(url,timeout=2).status_code==200:return
            except httpx.HTTPError:pass
            time.sleep(.5)
        raise RuntimeError('Local provider did not recover')
    try:
        docker('stop','mailpit')
        status=httpx.get('http://127.0.0.1:8000/api/automations/status',timeout=10).json()
        assert status['services']['mailpit']['reachable'] is False
        evidence['checks'].append('Stopped Mailpit reports unreachable, not healthy')
        print('PASS: Mailpit offline status is truthful',flush=True)
    finally:
        docker('start','mailpit');ready('http://127.0.0.1:8025/api/v1/info')
    key='offline-provider-'+uuid4().hex[:10]
    try:
        docker('stop','n8n')
        response=httpx.post('http://127.0.0.1:8000/api/automations/recovery',json={'idempotency_key':key,'lead_ids':[]},timeout=50)
        assert response.status_code==503
        runs=httpx.get('http://127.0.0.1:8000/api/automations/runs').json()
        run=next(r for r in runs if key in r['idempotency_key'])
        assert run['status']=='failed'
        evidence['checks'].append('Stopped n8n returns 503 and records a failed trigger without invented success')
        evidence['failed_trigger_run_id']=run['run_id']
        print('PASS: n8n outage fails visibly and persists a failed trigger run',flush=True)
    finally:
        docker('start','n8n');ready('http://127.0.0.1:5678/healthz')
    status=httpx.get('http://127.0.0.1:8000/api/automations/status',timeout=10).json()
    assert all(s['reachable'] for s in status['services'].values()) and not status['external_email_enabled']
    evidence['checks'].append('Both providers restored; external email still disabled')
    evidence['result']='passed'
    (ROOT/'data/processed/phase3_service_failures.json').write_text(json.dumps(evidence,indent=2))
    print('PASS: services restored; no external sending enabled',flush=True)


if __name__=='__main__':main()
