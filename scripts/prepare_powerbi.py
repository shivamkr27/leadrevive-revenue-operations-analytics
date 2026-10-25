"""Create a location-correct copy of the authored Phase 5 PBIP; preserve originals."""
import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.artifacts import verified_snapshot


def prepare(output, exports=None, generation=None):
    output=Path(output).resolve()
    if output.exists():raise ValueError('Output already exists; choose a new folder. Nothing overwritten.')
    if output.is_relative_to((ROOT/'analytics/powerbi').resolve()) or output.is_relative_to(Path(exports or ROOT/'analytics/exports').resolve()):
        raise ValueError('Choose an output outside preserved Power BI originals and immutable exports.')
    directory,snapshot=verified_snapshot(exports or ROOT/'analytics/exports',generation)
    source=ROOT/'analytics/powerbi/phase5'
    original=source/'LeadRevive.SemanticModel/model.bim'
    model=json.loads(original.read_text(encoding='utf-8'))
    mappings=[]
    for table in model['model']['tables']:
        for partition in table.get('partitions',[]):
            expression=partition.get('source',{}).get('expression')
            if not isinstance(expression,list):continue
            def replace(match):
                filename=match[1].replace('\\','/').rsplit('/',1)[-1]
                if filename not in json.loads((directory/'manifest.json').read_text())['files']:
                    raise ValueError('Unverified source requested: '+filename)
                target=directory/filename
                mappings.append({'table':table['name'],'file':filename})
                return 'File.Contents("'+target.as_posix().replace('"','""')+'")'
            partition['source']['expression']=[re.sub(r'File\.Contents\("([^"]+)"\)',replace,line) for line in expression]
    if len(mappings)!=6:raise ValueError('Expected six authored CSV inputs; review model changes.')
    output.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.powerbi-',dir=output.parent))
    try:
        shutil.copytree(source,staging,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.pbi','cache.abf','localSettings.json'))
        derived=staging/'LeadRevive.SemanticModel/model.bim'
        derived.write_text(json.dumps(model,indent=2),encoding='utf-8')
        proof={'origin':'SYNTHETIC','generation_id':snapshot['generation_id'],'data_revision':snapshot['data_revision'],
               'original_model_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
               'derived_model_sha256':hashlib.sha256(derived.read_bytes()).hexdigest(),'inputs':mappings,
               'verification':'Paths and source manifest verified; Desktop refresh/DAX for this derived copy is not claimed.'}
        (staging/'PORTABILITY.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
        staging.rename(output)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return proof


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'data/processed/powerbi_portable')
    parser.add_argument('--generation',default=None)
    args=parser.parse_args()
    proof=prepare(args.output,generation=args.generation)
    print(f"Open {args.output.resolve()/'LeadRevive.pbip'} in Power BI Desktop. Six verified CSV paths configured; original PBIX/PBIP unchanged.")
