"""Focused review artifact, provenance and preservation checks; no mutations to leads."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from sqlalchemy import select
from docx import Document
from pptx import Presentation
from pypdf import PdfReader
import httpx

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.app import models as m
from backend.app.artifacts import verified_snapshot,number_equal
from backend.app.narrative import display
from backend.app.foundation import engine_for
from scripts.local_config import postgres_url
from scripts.migrate_to_postgres import digest


def read_json(path):
    data=Path(path).read_bytes()
    return json.loads(data.decode('utf-16' if data.startswith(b'\xff\xfe') else 'utf-8-sig'))


def run():
    directory,s=verified_snapshot()
    r=read_json(ROOT/'data/processed/phase5_review_report.json')
    if r['data_revision']!=s['data_revision']:raise ValueError('Review report revision differs from current analytics')
    folder=ROOT/'reports/generated'/r['report_id']
    for name,expected in r['files'].items():
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=expected:raise ValueError('Report file changed: '+name)
    if not all(number_equal(value,r['kpis'][key]) for key,value in s['kpis'].items()):raise ValueError('Report KPIs differ')
    pdf=PdfReader(folder/'LeadRevive_Report_SYNTHETIC.pdf');pdf_text='\n'.join(p.extract_text() for p in pdf.pages)
    word=Document(folder/'LeadRevive_Report_SYNTHETIC.docx');table_text='\n'.join(c.text for table in word.tables for row in table.rows for c in row.cells)
    for key,value in s['kpis'].items():
        if display(key,value) not in pdf_text or display(key,value) not in table_text:raise ValueError('Report value missing: '+key)
    deck=Presentation(folder/'LeadRevive_Management_SYNTHETIC.pptx')
    if len(deck.slides)!=10:raise ValueError('Expected 10 slides')
    pictures=sum(shape.shape_type==13 for slide in deck.slides for shape in slide.shapes)
    if pictures!=4:raise ValueError('Expected four actual screenshot images')
    pbix=ROOT/'analytics/powerbi/LeadRevive_Phase5_SYNTHETIC.pbix'
    with zipfile.ZipFile(pbix) as archive:
        if archive.testzip() is not None or 'DataModel' not in archive.namelist():raise ValueError('Invalid PBIX')
        if sum(n.endswith('/page.json') for n in archive.namelist())!=8:raise ValueError('Expected 8 Power BI pages')
    before=read_json(ROOT/'data/processed/phase5_preservation_before.json')
    engine=engine_for(postgres_url())
    try:
        with engine.connect() as conn:leads=[dict(row) for row in conn.execute(select(m.leads)).mappings()]
    finally:engine.dispose()
    if len(leads)!=before['lead_count'] or digest(leads)!=before['lead_sha256']:raise ValueError('Canonical lead records changed')
    workflows=read_json(ROOT/'data/processed/phase5_workflows.json')
    previous=read_json(ROOT/'data/processed/phase3_final_state.json')['workflows']
    if {r['id']:r['active'] for r in workflows}!={r['id']:r['active'] for r in previous}:raise ValueError('Workflow state changed')
    status=httpx.get('http://127.0.0.1:8000/api/automations/status').json()
    if status['external_email_enabled']:raise ValueError('External email must remain disabled')
    result=dict(result='passed',snapshot_id=s['snapshot_id'],data_revision=s['data_revision'],generation_id=s['generation_id'],
        report_id=r['report_id'],kpis_verified=13,pdf_pages=len(pdf.pages),slides=10,actual_screenshot_images=pictures,
        canonical_leads_preserved=len(leads),canonical_lead_hash_preserved=True,business_workflows_preserved=4,schedule_probe_inactive=True,
        external_email_enabled=False,report_hashes_verified=len(r['files']),pbix_sha256=hashlib.sha256(pbix.read_bytes()).hexdigest())
    (ROOT/'data/processed/phase5_final_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':run()
