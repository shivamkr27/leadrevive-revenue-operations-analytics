"""Bootstrap only this project's local n8n owner, encrypted header credential and workflows."""
import json
import argparse
import time
import subprocess
import sys
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.local_config import local_config


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--if-needed',action='store_true',help='Preserve an already configured workflow set')
    parser.add_argument('--base-url',default='http://127.0.0.1:5678')
    parser.add_argument('--project',default=None)
    parser.add_argument('--compose-file',default=None)
    parser.add_argument('--env-file',default=None)
    args=parser.parse_args()
    config=local_config() if not args.env_file else dict(line.split('=',1) for line in Path(args.env_file).read_text().splitlines() if '=' in line and not line.startswith('#'))
    compose=['docker','compose']
    if args.env_file:compose+=['--env-file',args.env_file]
    if args.project:compose+=['-p',args.project]
    if args.compose_file:compose+=['-f',args.compose_file]
    deadline=time.monotonic()+45
    while True:
        try:
            if httpx.get(args.base_url+'/healthz',timeout=2).status_code==200:break
        except httpx.HTTPError:pass
        if time.monotonic()>deadline:raise RuntimeError('Local n8n did not become ready; no owner/workflow state changed.')
        time.sleep(.5)
    with httpx.Client(base_url=args.base_url,timeout=30) as client:
        setup=client.get('/rest/settings').json()['data']['userManagement']['showSetupOnFirstLoad']
        if setup:
            response=client.post('/rest/owner/setup',json=dict(email=config['N8N_OWNER_EMAIL'],
                firstName='Demo',lastName='Analyst',password=config['N8N_OWNER_PASSWORD']))
        else:
            response=client.post('/rest/login',json=dict(emailOrLdapLoginId=config['N8N_OWNER_EMAIL'],password=config['N8N_OWNER_PASSWORD']))
        if response.status_code!=200:
            raise RuntimeError(f'Local n8n owner setup/login failed ({response.status_code}); no credentials printed.')
        user=response.json()['data']
        user_id=user['id']
        if args.if_needed:
            exported=subprocess.run(compose+['exec','-T','n8n','n8n','export:workflow','--all','--output=/tmp/leadrevive-existing.json'],cwd=ROOT,capture_output=True,text=True)
            if exported.returncode:
                if 'No workflows found with specified filters' not in exported.stdout+exported.stderr:
                    raise RuntimeError('Cannot inspect existing local n8n workflows safely')
                ids=[]
            else:
                state=subprocess.run(compose+['exec','-T','n8n','node','-e',"console.log(JSON.stringify(JSON.parse(require('fs').readFileSync('/tmp/leadrevive-existing.json')).map(x=>x.id)))"],cwd=ROOT,capture_output=True,text=True,check=True)
                ids=json.loads(state.stdout)
            existing=[id_ in ids for id_ in ['LeadReviveIntake','LeadReviveRecovery','LeadReviveApproval','LeadReviveStatus']]
            if all(existing):
                print('Existing local n8n workflows preserved, including any intentional unpublished state.')
                return
            if any(existing):raise RuntimeError('Partial workflow set found. Review n8n before explicitly restoring exports with configure_n8n.py.')
    create="""const fs=require('fs');fs.writeFileSync('/tmp/leadrevive-credential.json',JSON.stringify([{id:'leadrevive-backend-header',name:'LeadRevive local shared header',type:'httpHeaderAuth',data:{name:'X-LeadRevive-Key',value:process.env.LEADREVIVE_WEBHOOK_SECRET}}]),{mode:0o600});"""
    def docker(*args):
        result=subprocess.run(compose+['exec','-T','n8n',*args],cwd=ROOT,capture_output=True,text=True)
        if result.returncode:
            # CLI diagnostics contain no credential values; never echo the temporary credential file.
            print(result.stdout[-2000:]);print(result.stderr[-2000:])
            raise RuntimeError('n8n CLI operation failed')
        print(result.stdout[-500:].strip())
    docker('node','-e',create)
    docker('n8n','import:credentials','--input=/tmp/leadrevive-credential.json','--userId='+user_id)
    docker('node','-e',"require('fs').unlinkSync('/tmp/leadrevive-credential.json')")
    docker('n8n','import:workflow','--separate','--input=/workflows','--userId='+user_id)
    for workflow_id in ['LeadReviveIntake','LeadReviveRecovery','LeadReviveApproval','LeadReviveStatus']:
        docker('n8n','publish:workflow','--id='+workflow_id)
    subprocess.run(compose+['restart','n8n'],cwd=ROOT,check=True)
    print('Local owner configured; header credential encrypted inside n8n; four workflows published. Secrets remain in ignored .env.')


if __name__=='__main__':main()
