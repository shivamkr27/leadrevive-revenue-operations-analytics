"""Run the same regression suite in isolated PostgreSQL schemas, preserving demo records."""
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.local_config import postgres_url

if __name__=='__main__':
    env=dict(os.environ,LEADREVIVE_TEST_POSTGRES_URL=postgres_url())
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s','backend/tests','-v'],cwd=ROOT,env=env)
    raise SystemExit(result.returncode)
