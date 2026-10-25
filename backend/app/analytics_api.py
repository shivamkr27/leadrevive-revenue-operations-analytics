"""Read-only access to the explicitly refreshed analytics snapshot."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.app.artifacts import verified_snapshot

EXPORTS=Path(__file__).resolve().parents[2]/'analytics/exports'
ALLOWED={'LeadRevive_Analysis_SYNTHETIC.xlsx','LeadFacts_SYNTHETIC.csv','KPI_SYNTHETIC.csv',
         'Sources_SYNTHETIC.csv','Owners_SYNTHETIC.csv','Stages_SYNTHETIC.csv',
         'Quality_SYNTHETIC.csv','Workflow_SYNTHETIC.csv','Operations_SYNTHETIC.csv',
         'Reconciliation_SYNTHETIC.csv','Experiment_SYNTHETIC.csv','ExperimentEvents_SYNTHETIC.csv',
         'ExperimentRules_SYNTHETIC.csv','experiment_engine_verification.json','manifest.json'}
router=APIRouter()


@router.get('/api/analytics/report')
def report(generation:str|None=None):
    try:directory,result=verified_snapshot(EXPORTS,generation)
    except (ValueError,FileNotFoundError,json.JSONDecodeError) as exc:
        raise HTTPException(409 if generation else 503,'Analytics generation unavailable or invalid; refresh/rebuild the pack.') from exc
    result.pop('facts',None)
    result['downloads']=sorted(ALLOWED)
    return result


@router.get('/api/analytics/export/{name}')
def download(name:str,generation:str|None=None):
    try:directory,snapshot=verified_snapshot(EXPORTS,generation)
    except (ValueError,FileNotFoundError,json.JSONDecodeError) as exc:
        raise HTTPException(409,'Analytics generation unavailable or invalid.') from exc
    if name not in ALLOWED or not (directory/name).is_file():
        raise HTTPException(404,'Analytics export not found.')
    return FileResponse(directory/name,filename=name)
