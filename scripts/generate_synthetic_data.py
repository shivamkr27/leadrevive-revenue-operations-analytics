"""Generate fictional, non-contactable LeadRevive import fixtures (stdlib only)."""
import argparse
import csv
import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AS_OF = datetime(2026, 10, 24, tzinfo=timezone.utc)
STAGES = ['New', 'Contacted', 'Qualified', 'Meeting', 'Proposal', 'Won', 'Lost']
SOURCES = ['Web', 'Referral', 'Event', 'InboundEmail', 'Manual']


def timestamp(value):
    return value.isoformat().replace('+00:00', 'Z') if value else ''


def generate(seed=42, count=800):
    if count < 1:
        raise ValueError('count must be positive')
    rng = random.Random(seed)
    rows = []
    for i in range(count):
        created = AS_OF - timedelta(hours=rng.randint(240, 4320))
        stage = rng.choices(STAGES, weights=[24, 20, 17, 10, 12, 9, 8])[0]
        contacted = None if stage == 'New' else created + timedelta(hours=rng.randint(1, 120))
        next_action = None if stage in ('Won', 'Lost') or i % 13 == 0 else AS_OF + timedelta(hours=rng.randint(-240, 120))
        row = dict(lead_id=f'SYN-{i+1:06d}', created_at=timestamp(created),
                   updated_at=timestamp(contacted or created), full_name=f'Fictional Contact {i+1:04d}',
                   company=f'Synthetic Business {i+1:04d}', email=f'lead{i+1:06d}@leadrevive.example',
                   phone=f'FICTIONAL-IN-{i+1:06d}', lead_source=SOURCES[i % 5],
                   campaign=f'SYNTHETIC Campaign {i % 6 + 1}',
                   industry=rng.choice(['IT Services', 'Training', 'Logistics']),
                   company_size=rng.choice(['1-10', '11-50', '51-200']),
                   estimated_deal_value_inr=str(rng.randrange(10, 501)*1000), stage=stage,
                   owner_id='' if i % 17 == 0 else f'REP-{i % 4 + 1}',
                   consent_to_email='false', email_verified='false',
                   last_contacted_at=timestamp(contacted), next_action_at=timestamp(next_action),
                   response_sla_hours='24', lost_reason=rng.choice(['Budget', 'Timing', 'Fit']) if stage == 'Lost' else '',
                   created_by='synthetic-generator', scenario_label='SYNTHETIC', fixture_case='valid')
        # Deterministic, disjoint fixture slots: retain every raw input for later rejection/audit.
        slot = i % 100
        if i >= 100 and slot == 0:
            row = dict(rows[i-100], fixture_case='exact_duplicate')
        elif slot == 1:
            row.update(email='invalid-address', fixture_case='invalid_email')
        elif slot == 2:
            row.update(company='', fixture_case='missing_company')
        elif slot == 3:
            row.update(stage='Unknown', fixture_case='unknown_stage')
        elif slot == 4:
            row.update(estimated_deal_value_inr='not-money', fixture_case='malformed_value')
        elif i >= 100 and slot == 5:
            row.update(email=rows[i-100]['email'], fixture_case='conflicting_identity')
        rows.append(row)
    return rows


def write_dataset(output, seed=42, count=800):
    rows = generate(seed, count)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / 'leads_SYNTHETIC.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    manifest = {'origin': 'SYNTHETIC', 'seed': seed, 'raw_row_count': count,
                'as_of_utc': timestamp(AS_OF), 'sha256': hashlib.sha256(csv_path.read_bytes()).hexdigest(),
                'fixture_counts': {case: sum(r['fixture_case'] == case for r in rows)
                                   for case in sorted({r['fixture_case'] for r in rows})}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    (output / 'DATA_PROVENANCE.md').write_text(
        '# SYNTHETIC data provenance\n\nAll identities and companies are numbered fiction. '
        'No source customer data is used. Email domains are reserved .example except intentional invalid fixtures. '
        'Phones contain FICTIONAL and are not dialable. Consent and verification are always false. '
        'Never send to these records. Raw rows include duplicates and invalid fixtures; raw count is not clean lead count. '
        'The fixed clock is 2026-10-24T00:00:00Z; overdue metrics must use an explicit evaluation time. '
        'manifest.json records seed, fixture counts and CSV SHA-256.\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--count', type=int, default=800)
    parser.add_argument('--output', type=Path, default=ROOT / 'data' / 'synthetic')
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    print(json.dumps(write_dataset(args.output, args.seed, args.count), indent=2))


if __name__ == '__main__':
    main()
