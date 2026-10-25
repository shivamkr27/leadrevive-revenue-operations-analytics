"""Read-only source-archive integrity and primary documentation link checks."""
import hashlib
import json
import posixpath
import re
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    version=(ROOT/'VERSION').read_text().strip()
    path=ROOT/'releases'/f'LeadRevive-v{version}-source.zip'
    expected=Path(str(path)+'.sha256').read_text().split()[0]
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('LeadRevive/RELEASE_MANIFEST.json'))
        names=set(manifest['files'])
        for name,digest in manifest['files'].items():
            assert '..' not in Path(name).parts
            assert hashlib.sha256(z.read('LeadRevive/'+name)).hexdigest()==digest,name
        required=['Dockerfile','docker-compose.yml','scripts/bootstrap_demo.py','scripts/start_local.ps1','data/synthetic/leads_SYNTHETIC.csv','analytics/exports/current.json','backend/tests/test_bootstrap.py','LICENSE','THIRD_PARTY_NOTICES.md','third_party/notices/README.md','scripts/prepare_powerbi.py',f'reports/portfolio/v{version}/LeadRevive_Management_SYNTHETIC.pptx',f'reports/portfolio/v{version}/LeadRevive_Report_SYNTHETIC.pdf','analytics/powerbi/LeadRevive_Phase5_SYNTHETIC.pbix','automation/n8n/workflows/intake.json','automation/n8n/workflows/overdue_recovery.json','automation/n8n/workflows/email_approval.json','automation/n8n/workflows/status_sync.json']
        assert all(name in names for name in required)
        assert not any(name.startswith(('data/processed/','data/backups/','reports/generated/')) or name=='.env' for name in names)
        primary=['README.md','docs/PHASE_6_REPORT.md','docs/SETUP.md','docs/RELEASE_CHECKLIST.md','docs/GIT_PUBLICATION.md','docs/PHASE_5_REPORT.md']
        checked=0
        for document in primary:
            text=z.read('LeadRevive/'+document).decode('utf-8')
            for target in re.findall(r'\]\(([^)]+)\)',text):
                if target.startswith(('http:','https:','#')):continue
                target=target.split('#')[0]
                resolved=posixpath.normpath(posixpath.join(posixpath.dirname(document),target))
                assert resolved in names or any(n.startswith(resolved.rstrip('/')+'/') for n in names),(document,target)
                checked+=1
    result={'result':'passed','version':version,'archive_sha256':expected,'files_verified':len(names),'primary_local_links_verified':checked,'runtime_and_credentials_excluded':True}
    (ROOT/'data/processed/phase6_archive_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
