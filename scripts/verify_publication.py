"""Compare the EXACT index/committed tree to the prepared source ZIP manifest."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPOSITORY='https://github.com/shivamkr27/leadrevive-revenue-operations-analytics.git'


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',help='Omit for the staged index');args=parser.parse_args()
    version=(ROOT/'VERSION').read_text().strip()
    manifest=json.loads((ROOT/'releases'/f'LeadRevive-v{version}-manifest.json').read_text())
    if args.revision:
        paths=set(git('ls-tree','-r','--name-only','-z',args.revision).decode().split('\0'))-{''}
        prefix=args.revision+':'
    else:
        paths=set(git('ls-files','--cached','-z').decode().split('\0'))-{''};prefix=':'
    assert paths==set(manifest['files']),{'extra':sorted(paths-set(manifest['files'])),'missing':sorted(set(manifest['files'])-paths)}
    for name,digest in manifest['files'].items():
        assert hashlib.sha256(git('show',prefix+name)).hexdigest()==digest,'Staged/committed bytes differ: '+name
    assert git('remote','get-url','origin').decode().strip()==REPOSITORY
    tag_matches=None
    if args.revision:
        tag_matches=git('rev-parse','v1.0.0^{commit}').strip()==git('rev-parse',args.revision).strip()
        assert tag_matches,'Release tag does not point to reviewed commit'
    result={'result':'passed','version':version,'repository':REPOSITORY,'tree':args.revision or 'index','files_matching_manifest':len(paths),'tag_matches_commit':tag_matches,'push_performed':False}
    (ROOT/'data/processed'/('final_publication_commit.json' if args.revision else 'final_publication_index.json')).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
