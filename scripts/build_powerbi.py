"""Author a real editable PBIP model/report from the canonical CSV snapshot.

Desktop must refresh/open/save PBIX and verify visuals before claiming completion.
"""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.artifacts import current_dir
from backend.app.analytics import FACT_FIELDS
BASE='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
OUT=ROOT/'analytics/powerbi/phase5'


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2),encoding='utf-8')


def literal(value):
    return {'expr':{'Literal':{'Value':value}}}


def projection(table,prop,measure=False):
    if measure:
        prop='KPI '+prop
    return dict(field={('Measure' if measure else 'Column'):dict(Expression={'SourceRef':{'Entity':table}},Property=prop)},
                queryRef=table+'.'+prop,nativeQueryRef=prop)


def visual(page,index,kind,title,roles,x,y,width,height):
    name=f'v{index:03}'
    query={role:{'projections':[projection(*p) for p in fields]} for role,fields in roles.items()}
    config=dict(visualType=kind,query={'queryState':query},
                visualContainerObjects={'title':[{'properties':{'show':literal('true'),'text':literal("'"+title.replace("'","''")+"'"),
                'fontSize':literal('12D'),'fontColor':{'solid':{'color':literal("'#214D40'")}}}}]})
    dump(page/'visuals'/name/'visual.json',{'$schema':BASE+'visualContainer/2.8.0/schema.json',
         'name':name,'position':dict(x=x,y=y,z=index,width=width,height=height,tabOrder=index),'visual':config})


def build():
    export_dir=current_dir()
    snapshot=json.loads((export_dir/'snapshot.json').read_text())
    modeldir=OUT/'LeadRevive.SemanticModel'; reportdir=OUT/'LeadRevive.Report'
    facts=snapshot['facts']
    numeric_int={'open','contacted','qualified','won','scheduled','overdue','response_sla_hours','sla_met','sla_breached','awaiting_within_sla','recovery_rule_eligible'}
    numeric_double={'estimated_value_inr','first_response_hours','pipeline_exposure_inr','priority_score'}
    specs=[('LeadFacts','LeadFacts',list(FACT_FIELDS)),('Operations','Operations',['metric','value']),
           ('Experiment','Experiment',list(snapshot['experiment']['summary'][0])),
           ('Reconciliation','Reconciliation',['metric','application','sql','csv','excel','difference','status']),
           ('Workflow','Workflow',['workflow','status','jobs','attempts']),
           ('Snapshot','ReadMe',['field','value'])]
    tables=[]
    for name,filename,cols in specs:
        types={col:('int64' if col in numeric_int or col in ['jobs','attempts'] or (name=='Experiment' and col in ['cohort','surfaced','followups_completed','overdue_remaining']) else
                    'double' if col in numeric_double or col in ['action_rate','application','sql','csv','excel','difference'] else 'string') for col in cols}
        # Operations values include a boolean; expose as text, individual KPI cards use facts.
        conversions=', '.join('{"'+col+'", '+('Int64.Type' if typ=='int64' else 'type number' if typ=='double' else 'type text')+'}' for col,typ in types.items())
        file=(export_dir/(filename+'_SYNTHETIC.csv')).as_posix()
        expression=['let',f'    Source = Csv.Document(File.Contents("{file}"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
                    '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
                    '    Clean = Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,Table.ColumnNames(Headers)),',
                    f'    Typed = Table.TransformColumnTypes(Clean, {{{conversions}}}, "en-US")', 'in','    Typed']
        tables.append(dict(name=name,columns=[dict(name=c,dataType=t,sourceColumn=c,summarizeBy='none',**({'formatString':'0.0000'} if name=='Reconciliation' and t=='double' else {'formatString':'0.0%'} if c=='action_rate' else {})) for c,t in types.items()],
            partitions=[dict(name=name,mode='import',source=dict(type='m',expression=expression))]))
    measures={
        'Lead count':('COALESCE(COUNTROWS(LeadFacts),0)','0'),
        'Contacted':('COALESCE(SUM(LeadFacts[contacted]),0)','0'),
        'Uncontacted':('[Lead count]-[Contacted]','0'),
        'Qualified':('COALESCE(SUM(LeadFacts[qualified]),0)','0'),
        'Won':('COALESCE(SUM(LeadFacts[won]),0)','0'),
        'Open leads':('SUM(LeadFacts[open])','0'),
        'Scheduled':('COALESCE(SUM(LeadFacts[scheduled]),0)','0'),
        'Overdue':('COALESCE(SUM(LeadFacts[overdue]),0)','0'),
        'Response coverage':('DIVIDE([Contacted],[Lead count])','0.0%'),
        'Qualified rate':('DIVIDE([Qualified],[Lead count])','0.0%'),
        'Win rate':('DIVIDE([Won],[Lead count])','0.0%'),
        'Overdue rate':('DIVIDE([Overdue],[Scheduled])','0.0%'),
        'Median response hours':('MEDIAN(LeadFacts[first_response_hours])','0.0'),
        'Pipeline exposure INR':('COALESCE(SUM(LeadFacts[pipeline_exposure_inr]),0)','₹ #,##0'),
        'SLA met':('SUM(LeadFacts[sla_met])','0'),
        'SLA breached':('SUM(LeadFacts[sla_breached])','0'),
        'Awaiting within SLA':('SUM(LeadFacts[awaiting_within_sla])','0'),
        'Rule eligible':('SUM(LeadFacts[recovery_rule_eligible])','0')}
    def prefixed(expression):
        for measure in measures:
            expression=expression.replace('['+measure+']','[KPI '+measure+']')
        return expression
    tables[0]['measures']=[dict(name='KPI '+n,expression=prefixed(e),formatString=f) for n,(e,f) in measures.items()]
    def named(name):return next(t for t in tables if t['name']==name)
    named('Operations')['measures']=[dict(name='KPI '+label,expression=f'VALUE(CALCULATE(SELECTEDVALUE(Operations[value]),Operations[metric]="{key}"))',formatString='0')
        for label,key in [('Reminded leads','distinct_reminded_leads'),('Approvals','sink_only_approvals'),('Sink accepted','smtp_accepted_by_local_sink'),('Retried acceptance','accepted_after_retry')]]
    named('Workflow')['measures']=[dict(name='KPI Jobs',expression='SUM(Workflow[jobs])',formatString='0')]
    named('Experiment')['measures']=[dict(name='KPI Modeled contacts',expression='SUM(Experiment[followups_completed])',formatString='0'),
        dict(name='KPI Manual contacts',expression='CALCULATE(SUM(Experiment[followups_completed]),Experiment[arm]="manual")',formatString='0'),
        dict(name='KPI Scan contacts',expression='CALCULATE(SUM(Experiment[followups_completed]),Experiment[arm]="automation")',formatString='0')]
    metric_map={'new_leads':'Lead count','contacted':'Contacted','uncontacted':'Uncontacted','won':'Won','qualified':'Qualified',
        'active_scheduled':'Scheduled','overdue':'Overdue','first_response_coverage':'Response coverage','qualified_rate':'Qualified rate',
        'win_rate':'Win rate','overdue_rate':'Overdue rate','median_first_response_hours':'Median response hours','pipeline_exposure_inr':'Pipeline exposure INR'}
    dax='SWITCH(SELECTEDVALUE(Reconciliation[metric]),'+','.join(f'"{key}",[KPI {measure}]' for key,measure in metric_map.items())+')'
    named('Reconciliation')['measures']=[dict(name='KPI Actual DAX',expression=dax,formatString='0.0000'),
        dict(name='KPI SQL check',expression='VAR a=[KPI Actual DAX] VAR b=SELECTEDVALUE(Reconciliation[sql]) RETURN IF(NOT(HASONEVALUE(Reconciliation[metric])),BLANK(),IF(IF(ISBLANK(a),ISBLANK(b),NOT(ISBLANK(b)) && ABS(a-b)<0.00000001),"PASS","FAIL"))')]
    dump(modeldir/'definition.pbism',{'version':'1.0','settings':{}})
    dump(modeldir/'model.bim',dict(compatibilityLevel=1600,model=dict(culture='en-US',defaultPowerBIDataSourceVersion='powerBI_V3',
         sourceQueryCulture='en-US',tables=tables,annotations=[dict(name='LeadReviveSnapshot',value=snapshot['snapshot_id'])])))
    dump(reportdir/'definition.pbir',{'version':'4.0','datasetReference':{'byPath':{'path':'../LeadRevive.SemanticModel'}}})
    dump(OUT/'LeadRevive.pbip',{'version':'1.0','artifacts':[{'report':{'path':'LeadRevive.Report'}}],'settings':{'enableAutoRecovery':True}})
    definition=reportdir/'definition'
    dump(definition/'version.json',{'$schema':BASE+'versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    dump(definition/'report.json',{'$schema':BASE+'report/3.0.0/schema.json','themeCollection':{
         'baseTheme':{'name':'CY24SU10','reportVersionAtImport':{'visual':'1.8.50','page':'1.3.0','report':'2.0.0'},'type':'SharedResources'}}})
    pages=[('funnel','01 Funnel & stages'),('exposure','02 Follow-up exposure'),('source','03 Source performance'),
           ('owners','04 Owner workload'),('sla','05 Response SLA'),('evidence','06 Workflow evidence'),
           ('experiment','07 Modeled comparison'),('reconciliation','08 KPI reconciliation')]
    dump(definition/'pages/pages.json',{'$schema':BASE+'pagesMetadata/1.0.0/schema.json','pageOrder':[p[0] for p in pages],'activePageName':'funnel'})
    for pid,label in pages:
        page=definition/'pages'/pid
        dump(page/'page.json',{'$schema':BASE+'page/2.0.0/schema.json','name':pid,'displayName':label+' | SYNTHETIC',
             'displayOption':'FitToPage','width':1280,'height':720})
        i=0
        def add(kind,title,roles,x,y,w,h):
            nonlocal i
            i+=1;visual(page,i,kind,title,roles,x,y,w,h)
        def card(measure,title,x):add('card',title,{'Values':[('LeadFacts',measure,True)]},x,20,290,130)
        def chart(category,measures,title,x,y,w=600,h=420):
            add('clusteredBarChart',title,{'Category':[('LeadFacts',category,False)],'Y':[('LeadFacts',m,True) for m in measures]},x,y,w,h)
        def table(cols,title,x=25,y=180,w=1230,h=440):add('tableEx',title,{'Values':cols},x,y,w,h)
        if pid=='funnel':
            for j,(m,t) in enumerate([('Lead count','Synthetic lead cohort'),('Response coverage','First response coverage'),('Qualified rate','Ever qualified / cohort'),('Win rate','Current Won / cohort')]):card(m,t,20+j*310)
            chart('stage',['Lead count'],'Current stages (not sequential conversion)',20,180)
            chart('lead_source',['Qualified','Won'],'Qualified and Won by source',660,180)
        elif pid=='exposure':
            for j,(m,t) in enumerate([('Overdue','Overdue open leads'),('Scheduled','Scheduled open leads'),('Overdue rate','Overdue / scheduled'),('Pipeline exposure INR','Estimated pipeline exposure (not revenue)')]):card(m,t,20+j*310)
            chart('lead_source',['Pipeline exposure INR'],'Estimated overdue exposure by source',20,180)
            chart('owner',['Overdue'],'Overdue by owner, including unassigned',660,180)
        elif pid=='source':
            card('Lead count','Cohort · select source in chart',20)
            chart('lead_source',['Lead count','Contacted','Qualified','Won'],'Source cohort outcomes',20,180,740)
            add('slicer','Filter source',{'Values':[('LeadFacts','lead_source',False)]},820,180,400,420)
        elif pid=='owners':
            chart('owner',['Open leads','Overdue','Rule eligible'],'Owner workload (rule eligibility is before cooldown)',20,180,1230)
            card('Open leads','Open workload',20);card('Rule eligible','Business-rule eligible',330)
        elif pid=='sla':
            for j,(m,t) in enumerate([('SLA met','Contacted within elapsed-hour SLA'),('SLA breached','Late response + uncontacted breaches'),('Awaiting within SLA','Uncontacted within SLA'),('Median response hours','Median hours · contacted only')]):card(m,t,20+j*310)
            chart('lead_source',['SLA met','SLA breached','Awaiting within SLA'],'SLA partition by source',20,180,1230)
        elif pid=='evidence':
            for j,(measure,title) in enumerate([('Reminded leads','Distinct leads surfaced'),('Approvals','Manual sink-only approvals'),('Sink accepted','SMTP accepted by local sink'),('Retried acceptance','Accepted after retry')]):
                add('card',title,{'Values':[('Operations',measure,True)]},20+j*310,20,290,130)
            add('clusteredBarChart','Recorded jobs by workflow · latest states; includes induced faults',{'Category':[('Workflow','workflow',False)],'Y':[('Workflow','Jobs',True)]},20,180,720,410)
            table([('Workflow',c,False) for c in ['workflow','status','jobs','attempts']],'Jobs and attempts are different grains',770,180,485,410)
        elif pid=='experiment':
            add('card','Manual reviews · modeled contacts',{'Values':[('Experiment','Manual contacts',True)]},20,20,350,130)
            add('card','Hourly scans · modeled contacts',{'Values':[('Experiment','Scan contacts',True)]},410,20,350,130)
            add('clusteredBarChart','Identical 40-event cohort · assumed two-hour owner response',{'Category':[('Experiment','arm',False)],'Y':[('Experiment','Modeled contacts',True)]},20,180,600,410)
            table([('Experiment',c,False) for c in ['arm','cohort','followups_completed','overdue_remaining','action_rate']],
                  'Incomplete tasks are not the raw overdue KPI',650,180,600,410)
        elif pid=='reconciliation':
            table([('Reconciliation',c,False) for c in ['metric','application','sql','csv','excel']]+[('Reconciliation','Actual DAX',True),('Reconciliation','SQL check',True)],
                  '13 KPIs · independently calculated Desktop DAX vs frozen SQL · null-aware',25,35,1230,550)
        table([('Snapshot','field',False),('Snapshot','value',False)],'Snapshot provenance / definitions',25,635,1230,70)
    (OUT/'MEASURES.dax').write_text('\n\n'.join(f'KPI {n} = {prefixed(e)}' for n,(e,f) in measures.items()),encoding='utf-8')
    print('Created editable PBIP with 8 report pages; Desktop refresh and PBIX save still required.')


if __name__=='__main__':build()
