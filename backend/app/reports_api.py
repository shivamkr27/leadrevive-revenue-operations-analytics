"""Local on-demand reports pinned to one validated analytics generation."""
import json
from pathlib import Path
from typing import Literal
from fastapi import APIRouter,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel,ConfigDict,Field
from backend.app import reporting
from backend.app.artifacts import EXPORTS,verified_snapshot
from backend.app.analytics import build_snapshot
from backend.app.exporting import write_pack


class ReportRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    generation_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    mode:Literal['snapshot','fresh_cohort']='snapshot'
    start:str|None=None
    end:str|None=None


def create_router(engine,now,exports=None,report_root=None):
    exports=Path(exports or EXPORTS);report_root=Path(report_root or reporting.REPORTS)
    router=APIRouter()

    @router.get('/api/reports')
    def listing():
        paths=sorted(report_root.glob('*/metadata.json'),key=lambda p:p.stat().st_mtime,reverse=True)
        return {'reports':[json.loads(p.read_text(encoding='utf-8')) for p in paths[:20] if not p.parent.name.startswith('.')]}

    @router.post('/api/reports/generate')
    def generate(body:ReportRequest):
        try:
            verified_snapshot(exports,body.generation_id)
            generation=body.generation_id
            if body.mode=='fresh_cohort':
                if not body.start or not body.end:raise ValueError('Select start and exclusive end for a fresh PostgreSQL cohort')
                s=build_snapshot(engine,now(),body.start,body.end)
                generation=write_pack(s,exports,activate=False).name
            elif body.start or body.end:raise ValueError('Date changes require fresh cohort mode')
            return reporting.generate(generation,exports,report_root)
        except (ValueError,FileNotFoundError,json.JSONDecodeError) as exc:
            raise HTTPException(409,str(exc)) from exc

    @router.get('/api/reports/{report_id}/download/{name}')
    def download(report_id:str,name:str):
        try:
            metadata=reporting.report_metadata(report_id,report_root)
            if Path(name).name!=name or (name not in metadata['files'] and name!='metadata.json'):
                raise ValueError('Report file is not allowlisted')
            path=report_root/report_id/name
            if name!='metadata.json' and reporting.sha(path)!=metadata['files'][name]:raise ValueError('Report integrity check failed')
            return FileResponse(path,filename=name)
        except (ValueError,FileNotFoundError,json.JSONDecodeError) as exc:
            raise HTTPException(404,str(exc)) from exc
    return router
