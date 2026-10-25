"""Phase 1 validation, ingestion, priority and reproducible analytics."""
import csv
import hashlib
import io
import json
import math
import re
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from sqlalchemy import create_engine, event, select, or_, text
from backend.app import models as m

STAGES = ['New', 'Contacted', 'Qualified', 'Meeting', 'Proposal', 'Won', 'Lost']
OPEN = STAGES[:5]
WEIGHTS = dict(overdue=35, value=25, stage=20, contactability=10, recency=10)


def engine_for(url):
    engine = create_engine(url,pool_pre_ping=True)
    if engine.dialect.name == 'sqlite':
        @event.listens_for(engine, 'connect')
        def foreign_keys(dbapi_connection, _):
            dbapi_connection.execute('PRAGMA foreign_keys=ON')
    return engine


def iso(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timestamp must include UTC offset')
    return parsed.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def dt(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def normalize(row):
    """Reject ambiguity; do not infer consent, owners, stages or timestamps."""
    errors = []
    result = {}
    required = ['lead_id', 'created_at', 'updated_at', 'full_name', 'company', 'email',
                'phone', 'lead_source', 'campaign', 'industry', 'company_size', 'stage',
                'created_by', 'scenario_label']
    for field in required:
        result[field] = str(row.get(field) or '').strip()
        if not result[field]:
            errors.append(field + ': required')
    result['email'] = result['email'].casefold()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', result['email']):
        errors.append('email: invalid format')
    # Keep fictional phone tokens; normalize actual Indian numbers only in explicit IN context.
    phone = result['phone']
    if not phone.startswith('FICTIONAL-IN-'):
        digits = re.sub(r'[^0-9]', '', phone)
        if digits.startswith('91') and len(digits) == 12:
            result['phone'] = '+' + digits
        else:
            errors.append('phone: require explicit +91 country context or fictional token')
    if result['stage'] not in STAGES:
        errors.append('stage: unknown stage')
    if result['lead_source'] not in ['Web', 'Referral', 'Event', 'InboundEmail', 'Manual']:
        errors.append('lead_source: unknown source')
    if result['scenario_label'] != 'SYNTHETIC':
        errors.append('scenario_label: Phase 1 accepts SYNTHETIC only')
    for field in ['created_at', 'updated_at', 'last_contacted_at', 'next_action_at']:
        try:
            result[field] = iso(row[field]) if row.get(field) else None
            if field in ('created_at', 'updated_at') and result[field] is None:
                raise ValueError('required')
        except (ValueError, TypeError):
            errors.append(field + ': require timezone-aware ISO timestamp')
    if not any(e.startswith(('created_at:', 'updated_at:', 'last_contacted_at:')) for e in errors):
        if result['updated_at'] < result['created_at']:
            errors.append('updated_at: before creation')
        if result['last_contacted_at'] and result['last_contacted_at'] < result['created_at']:
            errors.append('last_contacted_at: before creation')
        if result['last_contacted_at'] and result['last_contacted_at'] > result['updated_at']:
            errors.append('last_contacted_at: after last update')
    # The generator records one initial contact; do not infer first response from last contact for live data.
    result['first_contacted_at'] = result['last_contacted_at']
    for field in ['consent_to_email', 'email_verified']:
        value = str(row.get(field, 'false')).strip().lower()
        if value not in ['true', 'false', '']:
            errors.append(field + ': require true/false')
        result[field] = value == 'true'
    try:
        value = Decimal(str(row.get('estimated_deal_value_inr', '')))
        if not value.is_finite() or value < 0 or value > Decimal('1000000000000') or value.as_tuple().exponent < -2:
            raise ValueError()
        result['estimated_value_paise'] = int(value * 100)
    except (ValueError, InvalidOperation):
        errors.append('estimated_deal_value_inr: require nonnegative INR with at most two decimals')
    try:
        result['response_sla_hours'] = int(row.get('response_sla_hours', 24))
        if not 1 <= result['response_sla_hours'] <= 720:
            raise ValueError()
    except (ValueError, TypeError):
        errors.append('response_sla_hours: require integer from 1 to 720')
    result.update(owner_id=row.get('owner_id') or None, lost_reason=row.get('lost_reason') or None,
                  suppressed=False, version=1)
    return result, errors


def record_event(conn, table, lead_id, event_type, details, now):
    conn.execute(table.insert().values(event_id=str(uuid4()), lead_id=lead_id,
        created_at=now, event_type=event_type, details_json=json.dumps(details, sort_keys=True)))


def import_csv(engine, path, now):
    now = iso(now)
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    summary = dict(accepted=0, invalid=0, duplicates=0, review_required=0)
    with engine.begin() as conn:
        existing = conn.execute(select(m.import_batches).where(m.import_batches.c.sha256 == digest)).mappings().first()
        if existing:
            return dict(json.loads(existing['summary_json']), batch_id=existing['batch_id'], replay=True)
        batch_id = str(uuid4())
        conn.execute(m.import_batches.insert().values(batch_id=batch_id, sha256=digest,
            created_at=now, summary_json='{}'))
        owners = set(conn.execute(select(m.owners.c.owner_id).where(m.owners.c.active.is_(True))).scalars())
        reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
        if not reader.fieldnames or 'lead_id' not in reader.fieldnames:
            raise ValueError('CSV header must include lead_id')
        for number, raw in enumerate(reader, start=2):
            row, errors = normalize(raw)
            if not errors and (row['created_at'] > now or row['updated_at'] > now):
                errors.append('created_at/updated_at: cannot be in the future')
            if row['owner_id'] and row['owner_id'] not in owners:
                errors.append('owner_id: unknown or inactive owner')
            matches = [] if errors else conn.execute(select(m.leads).where(or_(
                m.leads.c.lead_id == row['lead_id'], m.leads.c.email == row['email'],
                m.leads.c.phone == row['phone']))).mappings().all()
            if errors:
                summary['invalid'] += 1
                reason = '; '.join(errors)
            elif matches:
                same = len(matches) == 1 and all(matches[0][key] == value for key, value in row.items())
                kind = 'duplicates' if same else 'review_required'
                summary[kind] += 1
                reason = 'exact duplicate; existing record preserved' if same else 'identity collision; manual review required'
                record_event(conn, m.lead_merge_audit, matches[0]['lead_id'], kind,
                    dict(batch_id=batch_id, row_number=number, candidate_ids=[r['lead_id'] for r in matches]), now)
            else:
                conn.execute(m.leads.insert().values(**row))
                summary['accepted'] += 1
                for table, kind in [(m.lead_activities, 'imported'), (m.lead_status_history, 'initial_stage'),
                                    (m.audit_events, 'lead_created')]:
                    record_event(conn, table, row['lead_id'], kind, dict(batch_id=batch_id, stage=row['stage']), now)
                continue
            conn.execute(m.import_rejections.insert().values(rejection_id=str(uuid4()), batch_id=batch_id,
                row_number=number, reason=reason, raw_json=json.dumps(raw)))
        conn.execute(m.import_batches.update().where(m.import_batches.c.batch_id == batch_id).values(summary_json=json.dumps(summary)))
    return dict(summary, batch_id=batch_id, replay=False)


def priority(lead, as_of, values, weights=None):
    weights = WEIGHTS if weights is None else weights
    if set(weights) != set(WEIGHTS) or any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in weights.values()) or sum(weights.values()) != 100:
        raise ValueError('weights must be nonnegative finite numbers totaling 100')
    now = dt(iso(as_of))
    overdue = max(0, (now-dt(lead['next_action_at'])).total_seconds()/3600) if lead.get('next_action_at') else 0
    value = lead.get('estimated_value_paise', 0)
    # Midrank percentile handles tied values without assigning every tie maximum priority.
    percentile = (sum(v < value for v in values)+0.5*sum(v == value for v in values))/len(values) if values else 0
    factors = dict(overdue=min(overdue/168, 1), value=percentile,
        stage={'New': .1, 'Contacted': .25, 'Qualified': .5, 'Meeting': .75, 'Proposal': 1}.get(lead['stage'], 0),
        contactability=float(bool(lead.get('email_verified')) and not lead.get('suppressed', False)),
        recency=max(0, 1-(now-dt(lead['last_contacted_at'])).total_seconds()/86400/30) if lead.get('last_contacted_at') else 0)
    factors['recency'] = min(1, factors['recency'])
    breakdown = {key: round(weights[key]*factors[key], 4) for key in weights}
    return dict(score=round(sum(breakdown.values()), 2), breakdown=breakdown,
        missing=[key for key, field in [('overdue', 'next_action_at'), ('recency', 'last_contacted_at')] if not lead.get(field)])


def sla_status(lead, as_of):
    due = dt(lead['created_at']) + timedelta(hours=lead['response_sla_hours'])
    first = dt(lead['first_contacted_at']) if lead.get('first_contacted_at') else None
    now = dt(iso(as_of))
    return dict(due_at=iso(due.isoformat()), basis='elapsed_hours',
                breached=(first > due) if first and first <= now else now > due,
                responded=bool(first and first <= now))


def recovery_candidates(conn, as_of):
    """Phase 1 candidate set; delivery cooldown is applied by Phase 3 service."""
    return conn.execute(select(m.leads).join(m.owners).where(
        m.leads.c.stage.in_(OPEN), m.owners.c.active.is_(True),
        m.leads.c.suppressed.is_(False), m.leads.c.next_action_at < iso(as_of)
    )).mappings().all()


def kpis(engine, as_of, start='1900-01-01T00:00:00Z', end='2100-01-01T00:00:00Z', source=None):
    import statistics
    now, begin, finish = iso(as_of), iso(start), iso(end)
    if begin >= finish:
        raise ValueError('start must be before end')
    with engine.connect() as conn:
        query = select(m.leads).where(m.leads.c.created_at >= begin,
            m.leads.c.created_at < finish, m.leads.c.created_at <= now)
        if source:
            query = query.where(m.leads.c.lead_source == source)
        rows = conn.execute(query).mappings().all()
        ids = {r['lead_id'] for r in rows}
        contacted = [r for r in rows if r['first_contacted_at'] and r['first_contacted_at'] <= now]
        scheduled = [r for r in rows if r['stage'] in OPEN and r['next_action_at']]
        overdue = [r for r in scheduled if r['next_action_at'] < now]
        times = [(dt(r['first_contacted_at'])-dt(r['created_at'])).total_seconds()/3600 for r in contacted]
        qualified_stages = ['Qualified','Meeting','Proposal','Won']
        qualified = {r['lead_id'] for r in rows if r['stage'] in qualified_stages}
        for history in conn.execute(select(m.lead_status_history).where(m.lead_status_history.c.created_at <= now)).mappings():
            details = json.loads(history['details_json'])
            if history['lead_id'] in ids and details.get('stage') in qualified_stages:
                qualified.add(history['lead_id'])
        count = len(rows)
        won = sum(r['stage'] == 'Won' for r in rows)
        return dict(new_leads=count, contacted=len(contacted), won=won,
            uncontacted=count-len(contacted),
            first_response_coverage=len(contacted)/count if count else None,
            median_first_response_hours=statistics.median(times) if times else None,
            active_scheduled=len(scheduled), overdue=len(overdue),
            overdue_rate=len(overdue)/len(scheduled) if scheduled else None,
            pipeline_exposure_inr=sum(r['estimated_value_paise'] for r in overdue)/100,
            qualified=len(qualified), qualified_rate=len(qualified)/count if count else None,
            win_rate=won/count if count else None, as_of_utc=now, origin='SYNTHETIC')
