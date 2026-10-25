"""Prepare a local versioned source/evidence archive. Never commits, tags or publishes."""
import hashlib
import io
import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION=(ROOT/'VERSION').read_text().strip()
PORTFOLIO=ROOT/'reports/portfolio'/('v'+VERSION)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    PORTFOLIO.mkdir(parents=True,exist_ok=True)
    review_path=ROOT/'data/processed/phase5_review_report.json'
    if not review_path.exists():review_path=PORTFOLIO/'metadata.json'
    review=json.loads(review_path.read_text(encoding='utf-8'))
    source=ROOT/'reports/generated'/review['report_id']
    if not source.exists():source=PORTFOLIO
    for name,digest in review['files'].items():
        assert sha(source/name)==digest,'Reviewed artifact hash differs: '+name
        if source!=PORTFOLIO:shutil.copy2(source/name,PORTFOLIO/name)
    if source!=PORTFOLIO:shutil.copy2(source/'metadata.json',PORTFOLIO/'metadata.json')
    preview=ROOT/'reports/previews'/review['report_id']/'Management_Office_Preview.pdf'
    if preview.exists():shutil.copy2(preview,PORTFOLIO/preview.name)
    (PORTFOLIO/'README.md').write_text(f'''# Representative synthetic management pack — v{VERSION}

These are the reviewed snapshot-bound files, retained separately from ignored on-demand runtime output. Open LeadRevive_Management_SYNTHETIC.pptx (editable 10 slides), LeadRevive_Report_SYNTHETIC.pdf (two pages) or LeadRevive_Report_SYNTHETIC.docx (editable). Management_Office_Preview.pdf is an actual PowerPoint rendering. Metadata records hashes, screenshot provenance and the formatting revision.

Snapshot `9a80207b950500a9`; 758 synthetic records, including four retained integration fixtures. Estimated pipeline exposure is not recovered revenue. The 20 versus 34 result is modeled under stated assumptions. SMTP accepted by local sink only; external live delivery disabled. Documents preserve their Phase 5 review-gate wording as historical artifacts; Phase 6 status is in docs/PHASE_6_REPORT.md.

New installs have 754 seed leads; this frozen pack does not claim to match a newly initialized live database. Generate a new pack through Reports to analyze another cohort. All source screenshots remain in screenshots/; editable analytics/workflows remain in analytics/ and automation/.
''',encoding='utf-8')
    evidence=ROOT/'docs/evidence';evidence.mkdir(exist_ok=True)
    for name in ['phase6_integrity.json','phase6_integration.json','phase6_qa_verification.json','phase6_browser.json']:
        source_evidence=ROOT/'data/processed'/name
        if not source_evidence.exists():source_evidence=evidence/name
        content=json.loads(source_evidence.read_text(encoding='utf-8'))
        assert content['result']=='passed'
        (evidence/name).write_text(json.dumps(content,indent=2),encoding='utf-8')
    for old,new in [('phase5_final_verification.json','phase6_report_artifacts.json'),('phase4_pack_verification.json','phase6_analytics_pack.json')]:
        source_evidence=ROOT/'data/processed'/old
        if not source_evidence.exists():source_evidence=evidence/new
        content=json.loads(source_evidence.read_text(encoding='utf-8'))
        assert content['result']=='passed'
        (evidence/new).write_text(json.dumps(content,indent=2),encoding='utf-8')
    suites=json.loads((evidence/'phase6_regressions.json').read_text()) if (evidence/'phase6_regressions.json').exists() else {}
    for kind in ['sqlite','postgres','frontend']:
        log_path=ROOT/'data/processed'/f'phase6_{kind}_tests.log'
        if not log_path.exists():
            assert kind in suites,'Missing saved regression evidence'
            continue
        raw=log_path.read_bytes()
        log=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig',errors='replace').replace('\r\n','\n')
        if kind=='frontend':
            match=re.search(r'(\d+) passed \(([^)]+)\)',log);assert match
            suites[kind]={'passed':int(match[1]),'duration':match[2]}
        else:
            match=re.search(r'Ran (\d+) tests in ([\d.]+)s',log);assert match and re.search(r'^OK(?: \(skipped=\d+\))?$',log,re.M)
            skipped=re.search(r'OK \(skipped=(\d+)\)',log);n=int(skipped[1]) if skipped else 0
            suites[kind]={'run':int(match[1]),'passed':int(match[1])-n,'skipped':n,'seconds':float(match[2])}
    (evidence/'phase6_regressions.json').write_text(json.dumps(suites,indent=2))
    final_log=ROOT/'data/processed/phase6_final_targeted_retry.log'
    if final_log.exists():
        raw=final_log.read_bytes();log=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig').replace('\r\n','\n')
        match=re.search(r'Ran (\d+) tests in ([\d.]+)s',log);assert match and '\nOK (skipped=1)' in log
        (evidence/'phase6_final_targeted.json').write_text(json.dumps({'run':int(match[1]),'passed':int(match[1])-1,'skipped':1,'seconds':float(match[2]),'scope':'two new bootstrap safeguards plus final report/layout checks; overlaps prior reporting suite'},indent=2))
    result=subprocess.run(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT,capture_output=True,check=True)
    candidates=sorted(set(result.stdout.decode().split('\0'))-{''})
    allowed_roots=('backend/','frontend/','automation/','analytics/','data/synthetic/','docs/','reports/templates/','reports/portfolio/','screenshots/','scripts/','third_party/')
    allowed_files={'.dockerignore','.env.example','.gitignore','.gitattributes','Dockerfile','docker-compose.yml','alembic.ini','requirements.txt','requirements-dev.txt','README.md','VERSION','PROJECT_1_CODEX_MASTER_SPEC.md','LICENSE','THIRD_PARTY_NOTICES.md'}
    files=[name for name in candidates if name in allowed_files or name.startswith(allowed_roots)]
    values=[]
    for env in [ROOT/'.env',ROOT/'data/processed/phase6_qa/.env']:
        if env.exists():
            for line in env.read_text().splitlines():
                if '=' in line:
                    key,value=line.split('=',1)
                    if any(token in key for token in ['PASSWORD','SECRET','ENCRYPTION']) and len(value)>=12:values.append(value.encode())
    problems=[]
    private_profile=re.compile(rb'(?i)[a-z]:[\\/]+Users[\\/]+'+re.escape(Path.home().name.encode())+rb'(?:[\\/]|\b)')
    def scan(name,data,depth=0):
        decoded=[data]
        for encoding in ['utf-16-le','utf-16-be']:
            try:decoded.append(data.decode(encoding).encode('utf-8'))
            except UnicodeError:pass
        if any(value in content for value in values for content in decoded):problems.append(name+': configured secret value')
        sensitive=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|sk-[A-Za-z0-9]{32,})')
        if any(sensitive.search(content) for content in decoded):problems.append(name+': token/private-key pattern')
        # Actual private profile paths, not general setup instructions or examples.
        if any(private_profile.search(content) for content in decoded):problems.append(name+': private user profile path')
        stream=io.BytesIO(data)
        if depth<2 and zipfile.is_zipfile(stream):
            with zipfile.ZipFile(stream) as z:
                for member in z.namelist():
                    content=z.read(member)
                    scan(name+'!'+member,content,depth+1)
    for name in files:
        assert not any(part in name.split('/') for part in ['node_modules','__pycache__','.git','.venv','test-results','playwright-report'])
        assert not name.endswith(('.sqlite','.log','.env'))
        scan(name,(ROOT/name).read_bytes())
    if problems:raise RuntimeError('Packaging scan failed: '+json.dumps(problems))
    out=ROOT/'releases';out.mkdir(exist_ok=True)
    manifest={'version':VERSION,'repository':'https://github.com/shivamkr27/leadrevive-revenue-operations-analytics.git','project_license':'MIT; third-party exclusions and notices apply','created_at_utc':datetime.now(timezone.utc).isoformat(),'publication':'local preparation only; no push or GitHub release publication','origin':'SYNTHETIC','files':{name:sha(ROOT/name) for name in files},'secret_scan':{'eligible_files':len(files),'configured_secret_values_checked':len(values),'result':'passed','scope':'raw/UTF-16 and nested ZIP members (two levels), configured secrets and recognizable token/private-key patterns; not a general security or opaque-model PII audit'}}
    manifest_path=out/f'LeadRevive-v{VERSION}-manifest.json';manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    archive=out/f'LeadRevive-v{VERSION}-source.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in files:z.write(ROOT/name,'LeadRevive/'+name)
        z.write(manifest_path,'LeadRevive/RELEASE_MANIFEST.json')
    checksum=sha(archive);(out/(archive.name+'.sha256')).write_text(checksum+'  '+archive.name+'\n')
    print(json.dumps({'result':'passed','version':VERSION,'files':len(files),'archive':str(archive.relative_to(ROOT)),'sha256':checksum,'bytes':archive.stat().st_size,'publication':'none'},indent=2))


if __name__=='__main__':main()
