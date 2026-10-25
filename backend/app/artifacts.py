"""Immutable analytics generations with an atomic current-pointer commit."""
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EXPORTS=ROOT/'analytics/exports'


def number_equal(a,b,tolerance=1e-8):
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a)-float(b))<=tolerance


def revision(snapshot):
    excluded={'reconciliation','power_bi_verification','generation_id','data_revision','provenance','downloads'}
    payload={k:v for k,v in snapshot.items() if k not in excluded}
    provenance={'schema_version':'2','application_version':'0.5.0'}
    for name,path in [('domain','backend/app/analytics.py'),('model','scripts/build_powerbi.py'),('exporter','backend/app/exporting.py'),
                      ('experiment','scripts/run_phase4_experiment.py'),('foundation','backend/app/foundation.py'),
                      ('automation','backend/app/automation.py'),('operations','backend/app/operations.py')]:
        provenance[name+'_sha256']=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    payload['provenance']=provenance
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest(),provenance


def current_dir(root=EXPORTS,generation=None):
    root=Path(root)
    if generation is None:
        pointer=root/'current.json'
        if not pointer.exists():return root  # Preserved Phase 4 compatibility.
        generation=json.loads(pointer.read_text(encoding='utf-8'))['generation_id']
    if not re.fullmatch(r'[a-f0-9]{32}',generation):
        raise ValueError('Invalid analytics generation')
    directory=root/'generations'/generation
    if not (directory/'manifest.json').is_file():
        raise ValueError('Analytics generation not found')
    return directory


def atomic_json(path,payload):
    path=Path(path)
    fd,temp=tempfile.mkstemp(prefix='.pointer-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(payload,stream,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def verified_snapshot(root=EXPORTS,generation=None):
    directory=current_dir(root,generation)
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    for name,expected in manifest['files'].items():
        if Path(name).name!=name or hashlib.sha256((directory/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Analytics artifact integrity failed: '+name)
    snapshot=json.loads((directory/'snapshot.json').read_text(encoding='utf-8'))
    if snapshot['snapshot_id']!=manifest['snapshot_id']:
        raise ValueError('Snapshot identity mismatch')
    if snapshot.get('generation_id'):
        for key in ['generation_id','data_revision','provenance']:
            if snapshot[key]!=manifest.get(key):raise ValueError('Generation provenance mismatch')
        if snapshot['generation_id']!=directory.name:raise ValueError('Generation directory mismatch')
        excluded={'reconciliation','power_bi_verification','generation_id','data_revision','provenance','downloads'}
        payload={k:v for k,v in snapshot.items() if k not in excluded};payload['provenance']=snapshot['provenance']
        digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if digest!=snapshot['data_revision']:raise ValueError('Data revision mismatch')
    return directory,snapshot
