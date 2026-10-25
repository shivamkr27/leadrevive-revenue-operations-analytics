"""Read ignored local service configuration without printing credentials."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def local_config():
    path=ROOT/'.env'
    if not path.exists():
        raise RuntimeError('Run scripts/configure_phase3.py to generate local-only service secrets.')
    return dict(line.split('=',1) for line in path.read_text().splitlines()
                if line.strip() and not line.startswith('#') and '=' in line)


def postgres_url():
    return 'postgresql+psycopg://leadrevive:'+local_config()['POSTGRES_PASSWORD']+'@127.0.0.1:5433/leadrevive'
