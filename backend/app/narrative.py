"""Business interpretation from verified snapshot fields, with explicit assumptions."""
from collections import Counter

LABELS={'new_leads':'Leads in cohort','contacted':'First contacted','uncontacted':'Uncontacted','won':'Current Won',
 'qualified':'Ever qualified','active_scheduled':'Open with scheduled action','overdue':'Overdue follow-up',
 'first_response_coverage':'First-response coverage','qualified_rate':'Lead-to-qualified rate','win_rate':'Lead-to-win rate',
 'overdue_rate':'Overdue / scheduled open','median_first_response_hours':'Median first response (hours)',
 'pipeline_exposure_inr':'Estimated pipeline exposure (INR)'}


def display(key,value):
    if value is None:return 'N/A'
    if key.endswith('_rate') or key=='first_response_coverage':return f'{value:.1%}'
    return f'{value:,.1f}'.rstrip('0').rstrip('.') if isinstance(value,float) else f'{value:,}'


def business_findings(s):
    k=s['kpis'];facts=s['facts'];result=[]
    if not facts:return ['No leads match this creation cohort. Rates and response-time median are N/A; no sales outcome is inferred.']
    highest=max(s['sources'],key=lambda r:r['overdue']) if s['sources'] else None
    if highest:
        result.append(f"{highest['segment']} has the largest overdue count in this cohort: {highest['overdue']:,}, with INR {highest['pipeline_exposure_inr']:,.0f} estimated exposure. Review cohort age and capacity before changing source spend.")
    unassigned=[r for r in facts if r['owner_id']=='Unassigned' and r['overdue']]
    result.append(f"{len(unassigned):,} overdue leads are unassigned, representing INR {sum(r['pipeline_exposure_inr'] for r in unassigned):,.0f} estimated exposure. Owner reminders cannot resolve missing ownership.")
    result.append(f"Elapsed-hour SLA: {sum(r['sla_met'] for r in facts):,} met, {sum(r['sla_breached'] for r in facts):,} breached and {sum(r['awaiting_within_sla'] for r in facts):,} awaiting within SLA. The response median excludes {k['uncontacted']:,} uncontacted leads.")
    return result


def cost_scenarios(assumptions=None):
    a=dict(monthly_actions=200,hourly_capacity_value_inr=300,setup_hours=24,maintenance_hours_month=4,amortization_months=12)
    if assumptions:a.update(assumptions)
    rows=[]
    for minutes in [1,2,3]:
        hours=a['monthly_actions']*minutes/60
        gross=hours*a['hourly_capacity_value_inr']
        maintenance=a['maintenance_hours_month']*a['hourly_capacity_value_inr']
        setup=a['setup_hours']*a['hourly_capacity_value_inr']/a['amortization_months']
        rows.append(dict(assumed_minutes_saved_per_action=minutes,modeled_capacity_hours=round(hours,2),
                         gross_capacity_value_inr=round(gross,2),maintenance_value_inr=maintenance,
                         amortized_setup_value_inr=setup,net_capacity_equivalent_inr=round(gross-maintenance-setup,2)))
    return dict(assumptions=a,scenarios=rows,interpretation='Illustrative assumptions, not observed savings, cash flow, vendor prices or ROI. Hardware, electricity and licensing costs are not measured; capacity value is not revenue.')


def case_study(s):
    counts=Counter(r['cohort_kind'] for r in s['facts'])
    lines=['# LeadRevive — Business operations case study','',
        f"SYNTHETIC portfolio case | Snapshot {s['snapshot_id']} | Data revision {s.get('data_revision','legacy')} | Generation {s.get('generation_id','legacy')}",
        f"Evaluation: {s['as_of_utc']}; creation window [{s['window_start']}, {s['window_end']}). Current-state reporting; no historical reconstruction.",'',
        '## Problem and decision',
        'A B2B services team needs to see unowned enquiries, late first responses and missed next actions. The system helps a manager assign work and prioritize follow-up; it does not establish that overdue leads are lost sales.','',
        '## Method and cohort',
        f"PostgreSQL is canonical. Independent SQL and Python calculations reconcile before publication; CSV/Excel are read back. Power BI aggregates the derived facts. Cohort: {s['kpis']['new_leads']:,} leads ({counts['Seed dataset']:,} seed records; {counts['Controlled fixture']:,} controlled fixtures).",'',
        '| Measure | Snapshot value |','|---|---:|']
    lines += [f'| {LABELS[key]} | {display(key,value)} |' for key,value in s['kpis'].items()]
    lines += ['','## Findings and recommended actions']+['- '+finding for finding in business_findings(s)]
    lines += ['','## Automation and evidence',
        'Four workflows cover intake, recovery, approval-controlled outbox and status sync. Internal owner reminders are automated; customer-preview approval is manual and bound to exact content/version. External live delivery disabled.',
        'All-time local test ledger (not the selected lead cohort; includes deliberate fault tests):']
    for key in ['distinct_reminded_leads','sink_only_approvals','smtp_accepted_by_local_sink','accepted_after_retry','failed_or_uncertain_send_events']:
        lines.append(f"- {key.replace('_',' ')}: {s['operations'].get(key,0)}")
    lines += ['','## Controlled comparison',s['experiment']['assumptions'],
        'Owner actions are predetermined scenario assumptions. Application contact/recovery rules execute locally; n8n/SMTP receipt does not cause the simulated contacts.']
    for row in s['experiment']['summary']:
        lines.append(f"- {row['arm']}: {row['followups_completed']}/{row['cohort']} modeled contacts ({row['action_rate']:.0%}); {row['overdue_remaining']} incomplete due tasks.")
    lines += ['Raw overdue remains unchanged without next-action rescheduling. Local rule runtime is measured computation, not human time saved.','',
        '## Limits and next measurement',
        'Estimated pipeline exposure is neither recovered nor lost revenue. Current Won includes synthetic fixtures. Source comparisons are descriptive, not causal. Job counts include induced faults and retries; no production reliability or distributed exactly-once claim is made.',
        'A permissioned pilot should measure owner action and rescheduling rates, actual administrative effort, and recurring operating costs before making efficiency or financial claims. Local single-user scope only.','',
        '## Cost / benefit scenario',cost_scenarios()['interpretation'],
        'Assume 200 actions/month, INR 300/hour capacity value, 24 setup hours, 4 maintenance hours/month, amortized over 12 months. These are editable scenario inputs, not measurements.',
        '| Assumed minutes saved/action | Capacity hours/month | Net capacity-equivalent INR/month |',
        '|---:|---:|---:|']
    lines += [f"| {r['assumed_minutes_saved_per_action']} | {r['modeled_capacity_hours']} | {r['net_capacity_equivalent_inr']:,.0f} |" for r in cost_scenarios()['scenarios']]
    lines += ['', '## Evidence boundaries',
        'Historical Phase 3 evidence: 19 real integration checks. Phase 4 final regression: 51 PostgreSQL tests and 49 SQLite passes/two skips. These historical counts are not newly executed Phase 5 tests. Current report metadata records exact export and screenshot hashes.']
    return '\n'.join(lines)+'\n'
