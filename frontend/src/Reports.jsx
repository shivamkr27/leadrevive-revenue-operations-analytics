import React,{useState} from 'react';
export default function Reports({revision,tools}) {
 const {api,useRemote,Loading,ErrorBox}=tools;
 const snapshot=useRemote('/analytics/report',revision);
 const [mode,setMode]=useState('snapshot'),[start,setStart]=useState('2026-01-01'),[end,setEnd]=useState('2026-10-26');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[result,setResult]=useState(null),[refresh,setRefresh]=useState(0);
 const history=useRemote('/reports',refresh);
 async function generate(){
  setBusy(true);setError('');
  try {
   const body={generation_id:snapshot.data.generation_id,mode};
   if(mode==='fresh_cohort'){body.start=start+'T00:00:00Z';body.end=end+'T00:00:00Z';}
   const report=await api('/reports/generate',{method:'POST',body:JSON.stringify(body)});
   setResult(report);setRefresh(v=>v+1);
  }catch(e){setError(e.message);}finally{setBusy(false);}
 }
 if(snapshot.error)return <ErrorBox message={snapshot.error}/>;
 if(!snapshot.data)return <Loading/>;
 const s=snapshot.data;
 const links=report=><div className="report-downloads">{Object.keys(report.files).concat('metadata.json').map(name=><a key={name} className="button" href={`/api/reports/${report.report_id}/download/${encodeURIComponent(name)}`}>{name}</a>)}</div>;
 return <div className="analytics-page"><div className="page-heading"><div><span className="eyebrow">MANAGEMENT REPORTING · SYNTHETIC</span><h1>Reports & management briefing</h1><p>Generate editable Word, PowerPoint, PDF and the supporting case study from one validated snapshot.</p></div></div>
 <section className="panel"><h2>Choose the evidence basis</h2><p>Snapshot {s.snapshot_id} · evaluated {s.as_of_utc} · {s.kpis.new_leads} synthetic leads.</p><p>Creation window: {s.window_start} to {s.window_end} (end excluded). Estimated exposure is not recovered revenue.</p>
 <label>Report source <select aria-label="Report source" value={mode} onChange={e=>setMode(e.target.value)}><option value="snapshot">Validated analytics snapshot</option><option value="fresh_cohort">Fresh PostgreSQL creation cohort</option></select></label>
 {mode==='fresh_cohort'&&<div className="report-dates"><label>Created from (UTC)<input type="date" value={start} onChange={e=>setStart(e.target.value)}/></label><label>Created before (UTC)<input type="date" value={end} onChange={e=>setEnd(e.target.value)}/></label><p>A fresh cohort reads current records and validates SQL KPIs. It does not replace the Analytics snapshot. Screenshots appear only when evidence matches the report data.</p></div>}
 <p>Modeled outcomes, local workflow tests and assumed cost scenarios are labelled separately. External live delivery disabled.</p>
 <button className="button primary" disabled={busy||!s.generation_id} onClick={generate}>{busy?'Generating validated report…':'Generate report pack'}</button>
 {error&&<div role="alert" className="error">{error}</div>}</section>
 {result&&<section className="panel" aria-live="polite"><h2>Report pack ready</h2><p>Snapshot {result.snapshot_id} · revision {result.data_revision.slice(0,12)} · {result.kpis.new_leads} leads. Files and source hashes are recorded in metadata.</p>{links(result)}</section>}
 <section className="panel"><h2>Generated report history</h2>{history.error?<ErrorBox message={history.error}/>:!history.data?<Loading/>:history.data.reports.length===0?<p>No reports generated yet. Choose the evidence basis above.</p>:history.data.reports.map(r=><div className="report-history" key={r.report_id}><strong>{r.created_at_utc} · {r.kpis.new_leads} synthetic leads</strong><p>Snapshot {r.snapshot_id} · generation {r.generation_id}</p>{links(r)}</div>)}</section>
 </div>;
}
