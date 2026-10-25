"""Dedicated disposable browser-test database; never uses the demo workspace DB."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

if __name__=='__main__':
    os.chdir(ROOT)
    with tempfile.TemporaryDirectory(prefix='leadrevive-browser-') as folder:
        os.environ['DATABASE_URL']='sqlite:///'+(Path(folder)/'browser.sqlite').as_posix()
        # Seeder's aggregate JSON is intentionally kept inside the temporary directory,
        # while normal scripts still write their documented workspace exports.
        subprocess.run([sys.executable,str(ROOT/'scripts/seed_db.py'),'--export-dir',folder],check=True,env=os.environ)
        import uvicorn
        from backend.app.api import create_app
        uvicorn.run(create_app(fixed_now='2026-10-24T12:00:00Z'),host='127.0.0.1',port=8010)
