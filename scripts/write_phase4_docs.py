"""Generate a current case study; approved Phase 4 documents remain frozen."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.artifacts import verified_snapshot
from backend.app.narrative import case_study
if __name__=='__main__':
    _,snapshot=verified_snapshot()
    (ROOT/'docs/PHASE_5_CASE_STUDY.md').write_text(case_study(snapshot),encoding='utf-8')
    print('Generated snapshot-bound Phase 5 case study.')
