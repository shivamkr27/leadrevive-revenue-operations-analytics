"""Validate authored PBIR JSON against Microsoft schemas (network required)."""
import json
import sys
import urllib.request
from pathlib import Path
from jsonschema import Draft7Validator
from referencing import Registry, Resource

ROOT=Path(__file__).resolve().parents[1]
cache={}


def retrieve(uri):
    if uri not in cache:
        cache[uri]=json.load(urllib.request.urlopen(uri,timeout=30))
    return cache[uri]


if __name__=='__main__':
    checked=0;errors=[]
    base=ROOT/'analytics/powerbi/phase5/LeadRevive.Report/definition'
    if not base.exists():base=ROOT/'analytics/powerbi/LeadRevive.Report/definition'
    for path in base.rglob('*.json'):
        data=json.loads(path.read_text(encoding='utf-8'))
        uri=data.get('$schema')
        if not uri:raise ValueError('Missing schema: '+str(path))
        schema=retrieve(uri)
        registry=Registry(retrieve=lambda url:Resource.from_contents(retrieve(url))).with_resource(uri,Resource.from_contents(schema))
        validator=Draft7Validator(schema,registry=registry)
        errors.extend((str(path.relative_to(ROOT)),list(e.path),e.message) for e in validator.iter_errors(data))
        checked+=1
    print(json.dumps(dict(checked=checked,errors=errors),indent=2))
    raise SystemExit(bool(errors))
