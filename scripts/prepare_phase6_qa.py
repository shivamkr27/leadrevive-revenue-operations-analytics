"""Create a separate fresh Compose project, ports, credentials and bind outputs."""
import json
import secrets
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    qa=ROOT/'data/processed/phase6_qa'
    qa.mkdir(parents=True,exist_ok=True)
    if (qa/'compose.json').exists():raise RuntimeError('QA already prepared; inspect its state instead of resetting it.')
    values=dict(POSTGRES_PASSWORD=secrets.token_hex(24),N8N_ENCRYPTION_KEY=secrets.token_hex(32),LEADREVIVE_WEBHOOK_SECRET=secrets.token_hex(32),N8N_OWNER_EMAIL='owner@leadrevive.example',N8N_OWNER_PASSWORD='Lr!'+secrets.token_hex(20))
    env=qa/'.env';env.write_text('\n'.join(f'{k}={v}' for k,v in values.items())+'\n')
    command=['docker','compose','--env-file',str(env),'-f',str(ROOT/'docker-compose.yml'),'config','--format','json']
    result=subprocess.run(command,capture_output=True,text=True,check=True,cwd=ROOT)
    config=json.loads(result.stdout);config['name']='leadrevive-qa'
    ports={'postgres':{5432:15433},'backend':{8000:18000},'n8n':{5678:15678},'mailpit':{8025:18025,1025:11025}}
    for name,service in config['services'].items():
        for port in service['ports']:port['published']=str(ports[name][port['target']])
        for volume in service.get('volumes',[]):
            if volume['type']=='bind' and volume['target'] in ['/app/analytics/exports','/app/reports']:
                target=qa/('exports' if volume['target'].endswith('exports') else 'reports');target.mkdir(exist_ok=True)
                volume['source']=str(target)
        if name=='backend':service['image']='leadrevive-qa-backend:1.0.0-rc.1'
    for name,volume in config['volumes'].items():volume['name']='leadrevive-qa_'+name
    for name,network in config['networks'].items():network['name']='leadrevive-qa_'+name
    (qa/'compose.json').write_text(json.dumps(config,indent=2))
    print('Isolated QA configuration created; secrets hidden. Ports 18000 / 15678 / 18025 / 15433. Existing project untouched.')


if __name__=='__main__':main()
