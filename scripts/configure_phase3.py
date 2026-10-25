"""Generate local-only Docker/test credentials once. Never prints secret values."""
import secrets
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'.env'
existing=path.read_text() if path.exists() else ''
names={line.split('=',1)[0] for line in existing.splitlines() if '=' in line}
values=dict(POSTGRES_PASSWORD=secrets.token_hex(24),N8N_ENCRYPTION_KEY=secrets.token_hex(32),
            LEADREVIVE_WEBHOOK_SECRET=secrets.token_hex(32),
            N8N_OWNER_EMAIL='owner@leadrevive.example',N8N_OWNER_PASSWORD='Lr!'+secrets.token_hex(20),
            DRY_RUN='true',LIVE_EMAIL_ENABLED='false')
new=[f'{key}={value}' for key,value in values.items() if key not in names]
if new:
    path.write_text(existing.rstrip()+'\n'+'\n'.join(new)+'\n')
print('Local .env configured; values hidden. Existing settings preserved. External email remains disabled.')
