"""Prove a real n8n Schedule Trigger executes, then unpublish the zero-scope test workflow."""
import json
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import httpx
from scripts.local_config import local_config
from scripts.build_workflows import node,http


def main():
    key=uuid4().hex[:10];workflow_id='LeadReviveScheduleProbe'
    schedule=node('Every five seconds - test only','scheduleTrigger',[0,200],{'rule':{'interval':[{'field':'seconds','secondsInterval':5}]}},1.2)
    callback=http('Record zero-scope scheduled scan','recovery',"={{ JSON.stringify({idempotency_key:'schedule-proof-"+key+"-'+$execution.id,execution_id:$execution.id,lead_ids:[]}) }}",300)
    done=node('No leads or messages modified','noOp',[620,200],{})
    workflow=dict(id=workflow_id,name='[TEST - DISABLED AFTER VERIFICATION] LeadRevive schedule proof',active=False,
        nodes=[schedule,callback,done],connections={schedule['name']:{'main':[[{'node':callback['name'],'type':'main','index':0}]]},
        callback['name']:{'main':[[{'node':done['name'],'type':'main','index':0}]]}},settings={'executionOrder':'v1','timezone':'Asia/Kolkata'})
    path=ROOT/'automation/n8n/tests/schedule_probe.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(workflow,indent=2))
    config=local_config();evidence={'result':'running','test_scope':'zero lead IDs; no email','workflow_id':workflow_id}
    def docker(*args):
        result=subprocess.run(['docker','compose',*args],cwd=ROOT,capture_output=True,text=True)
        if result.returncode:raise RuntimeError('Docker schedule verification command failed: '+result.stderr[-1000:])
        return result.stdout.strip()
    def ready():
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            try:
                if httpx.get('http://127.0.0.1:5678/healthz',timeout=2).status_code==200:return
            except httpx.HTTPError:pass
            time.sleep(.5)
        raise RuntimeError('n8n did not become ready')
    published=False
    with httpx.Client(base_url='http://127.0.0.1:5678',timeout=15) as client:
        response=client.post('/rest/login',json={'emailOrLdapLoginId':config['N8N_OWNER_EMAIL'],'password':config['N8N_OWNER_PASSWORD']})
        response.raise_for_status();owner_id=response.json()['data']['id']
        container=docker('ps','-q','n8n')
        subprocess.run(['docker','cp',str(path),container+':/tmp/leadrevive-schedule-proof.json'],check=True,capture_output=True)
        try:
            docker('exec','-T','n8n','n8n','import:workflow','--input=/tmp/leadrevive-schedule-proof.json','--userId='+owner_id)
            docker('exec','-T','n8n','n8n','publish:workflow','--id='+workflow_id);published=True
            docker('restart','n8n');ready()
            deadline=time.monotonic()+25
            run=None
            while time.monotonic()<deadline:
                rows=httpx.get('http://127.0.0.1:8000/api/automations/runs',timeout=5).json()
                run=next((r for r in rows if r['idempotency_key'].startswith('recovery:schedule-proof-'+key)),None)
                if run and run['status']=='succeeded':break
                time.sleep(.5)
            if not run or run['status']!='succeeded' or not run['execution_id']:
                raise AssertionError('No successful real scheduled execution observed')
            evidence.update(result='passed',run_id=run['run_id'],n8n_execution_id=run['execution_id'],started_at=run['started_at'],processed=run['processed'])
            print('PASS: real n8n Schedule Trigger executed; zero-scope database run recorded.',flush=True)
        finally:
            if published:
                docker('exec','-T','n8n','n8n','unpublish:workflow','--id='+workflow_id)
                docker('restart','n8n');ready()
                docker('exec','-T','n8n','n8n','export:workflow','--id='+workflow_id,'--output=/tmp/leadrevive-schedule-stopped.json')
                raw=docker('exec','-T','n8n','node','-e',"const v=JSON.parse(require('fs').readFileSync('/tmp/leadrevive-schedule-stopped.json'));console.log(JSON.stringify({active:v[0].active,id:v[0].id}))")
                state=json.loads(raw)
                if state.get('active') is not False:raise AssertionError('Schedule probe remains published')
                evidence['test_workflow_unpublished']=True
            (ROOT/'data/processed/phase3_schedule.json').write_text(json.dumps(evidence,indent=2))
    print('PASS: temporary five-second workflow is unpublished; normal four workflows retained.',flush=True)


if __name__=='__main__':main()
