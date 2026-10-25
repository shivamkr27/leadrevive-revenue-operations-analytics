"""Read-only operational snapshot/compare. Never repairs or migrates the database."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from sqlalchemy import select,text,inspect
from backend.app import models as m
from backend.app.foundation import engine_for
from scripts.local_config import postgres_url
from scripts.migrate_to_postgres import digest


def capture():
    engine=engine_for(postgres_url());tables={}
    with engine.connect() as conn:
        conn.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        for table in m.metadata.sorted_tables:
            rows=[dict(r) for r in conn.execute(select(table)).mappings()]
            tables[table.name]={'count':len(rows),'sha256':digest(rows),'rows':rows}
        revision=conn.execute(text('SELECT version_num FROM alembic_version')).scalar()
        invalid=conn.execute(text('SELECT count(*) FROM pg_constraint WHERE contype=\'f\' AND NOT convalidated')).scalar()
    engine.dispose()
    command=['docker','compose','exec','-T','n8n']
    subprocess.run(command+['n8n','export:workflow','--all','--output=/tmp/phase6-state.json'],capture_output=True,check=True)
    result=subprocess.run(command+['node','-e',"console.log(JSON.stringify(JSON.parse(require('fs').readFileSync('/tmp/phase6-state.json')).map(x=>({id:x.id,active:x.active,nodes:x.nodes,connections:x.connections}))))"],capture_output=True,text=True,check=True)
    workflows=json.loads(result.stdout)
    return {'at_utc':datetime.now(timezone.utc).isoformat(),'tables':tables,'alembic_revision':revision,'unvalidated_foreign_keys':invalid,'workflows':workflows}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['before','after']);args=parser.parse_args()
    directory=ROOT/'data/processed';directory.mkdir(exist_ok=True,parents=True)
    state=capture();assert state['tables']['leads']['count']==758;assert state['unvalidated_foreign_keys']==0
    if args.mode=='before':
        (directory/'phase6_preservation_before.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
        print('Read-only baseline captured: 758 leads; all operational tables and workflow definitions.')
        return
    before=json.loads((directory/'phase6_preservation_before.json').read_text(encoding='utf-8'))
    results={}
    for table in m.metadata.sorted_tables:
        pk=[c.name for c in table.primary_key.columns]
        old=before['tables'][table.name];new=state['tables'][table.name]
        keys={tuple(row[k] for k in pk) for row in old['rows']}
        retained=[r for r in new['rows'] if tuple(r[k] for k in pk) in keys]
        assert digest(retained)==old['sha256'],f'Existing records changed: {table.name}'
        results[table.name]={'before':old['count'],'after':new['count'],'original_hash_preserved':True,'sha256':old['sha256']}
    assert digest(before['workflows'])==digest(state['workflows']),'Workflow definitions/state changed'
    result={'result':'passed','tables':results,'leads':758,'workflow_definitions_and_states_preserved':True,'alembic_revision':state['alembic_revision'],'unvalidated_foreign_keys':0,'method':'READ ONLY repeatable-read transactions; original primary-key row subsets hashed. No migration, seed or workflow execution against existing project.'}
    (directory/'phase6_integrity.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
