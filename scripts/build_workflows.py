"""Author four original n8n workflows. Exports contain credential references, no secrets."""
import json
from pathlib import Path
from uuid import uuid5,NAMESPACE_URL

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'automation/n8n/workflows'
CREDENTIAL={'httpHeaderAuth':{'id':'leadrevive-backend-header','name':'LeadRevive local shared header'}}


def node(name,type_,position,parameters,version=1,**extras):
    return dict(id=str(uuid5(NAMESPACE_URL,'leadrevive-node:'+name)),name=name,type='n8n-nodes-base.'+type_,
                typeVersion=version,position=position,parameters=parameters,**extras)


def hook(kind,y=220):
    return node('Authenticated '+kind+' webhook','webhook',[0,y],dict(httpMethod='POST',path='leadrevive/'+kind,
        authentication='headerAuth',responseMode='lastNode',options={}),2,
        webhookId='leadrevive-'+kind,credentials=CREDENTIAL)


def http(name,path,body,x,y=220):
    return node(name,'httpRequest',[x,y],dict(method='POST',url='http://backend:8000/api/integrations/n8n/'+path,
        authentication='genericCredentialType',genericAuthType='httpHeaderAuth',sendBody=True,
        specifyBody='json',jsonBody=body,options={'timeout':30000}),4.2,
        credentials=CREDENTIAL,retryOnFail=True,maxTries=3,waitBetweenTries=1000)


def condition(name,x):
    return node(name,'if',[x,220],{'conditions':{'options':{'caseSensitive':True,'leftValue':'','typeValidation':'strict','version':2},
        'conditions':[{'id':name+'-condition','leftValue':"={{ $json.status === 'succeeded' }}",'rightValue':'',
                       'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)


def make(filename,id_,name,nodes,edges):
    connections={}
    for src,dest,branch in edges:
        outputs=connections.setdefault(src,{'main':[]})['main']
        while len(outputs)<=branch:outputs.append([])
        outputs[branch].append({'node':dest,'type':'main','index':0})
    result=dict(id=id_,name=name,active=False,nodes=nodes,connections=connections,
        settings={'executionOrder':'v1','timezone':'Asia/Kolkata','saveManualExecutions':True},
        pinData={},tags=[])
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/(filename+'.json')).write_text(json.dumps(result,indent=2)+'\n')


def main():
    error=node('Stop and expose failure','stopAndError',[1140,460],{'errorMessage':"={{ $json.failure_reason || 'LeadRevive operation failed; inspect durable run and delivery logs.' }}"})
    done=node('Audited result','noOp',[1140,180],{})
    intake=hook('intake')
    job=http('Validate, deduplicate and assign','intake',"={{ JSON.stringify({idempotency_key:$json.body.idempotency_key, execution_id:$execution.id,lead:$json.body.lead}) }}",300)
    check=condition('Intake succeeded?',600)
    make('intake','LeadReviveIntake','LeadRevive W1 - Intake, validate and assign',[intake,job,check,done,error],
        [(intake['name'],job['name'],0),(job['name'],check['name'],0),(check['name'],done['name'],0),(check['name'],error['name'],1)])
    webhook=hook('recovery',340)
    schedule=node('Hourly recovery scan','scheduleTrigger',[0,80],{'rule':{'interval':[{'field':'hours','hoursInterval':1}]}},1.2)
    scan=http('Plan owner digests and reserve reminders','recovery',"={{ JSON.stringify({idempotency_key:$json.body?.idempotency_key || ('hourly-'+$execution.id),execution_id:$execution.id,...($json.body?.lead_ids ? {lead_ids:$json.body.lead_ids}:{})}) }}",300)
    check=condition('Scan succeeded?',550)
    send=http('Deliver current owner digests to Mailpit','dispatch',"={{ JSON.stringify({idempotency_key:'recovery-dispatch-'+$execution.id,execution_id:$execution.id,draft_ids:$json.draft_ids}) }}",790)
    delivered=condition('Sink accepted?',1020)
    final=node('Audited Mailpit result','noOp',[1280,180],{})
    error2=dict(error,position=[1280,460])
    make('overdue_recovery','LeadReviveRecovery','LeadRevive W2 - Overdue recovery and owner digests',
        [schedule,webhook,scan,check,send,delivered,final,error2],
        [(schedule['name'],scan['name'],0),(webhook['name'],scan['name'],0),(scan['name'],check['name'],0),
         (check['name'],send['name'],0),(check['name'],error2['name'],1),(send['name'],delivered['name'],0),
         (delivered['name'],final['name'],0),(delivered['name'],error2['name'],1)])
    webhook=hook('dispatch',340)
    schedule=node('Check approved outbox every five minutes','scheduleTrigger',[0,80],{'rule':{'interval':[{'field':'minutes','minutesInterval':5}]}},1.2)
    dispatch=http('Check approval, reconcile Message-ID and send to sink','dispatch',"={{ JSON.stringify({idempotency_key:$json.body?.idempotency_key || ('outbox-'+$execution.id),execution_id:$execution.id,...($json.body?.draft_ids ? {draft_ids:$json.body.draft_ids}:{}),force_retry:$json.body?.force_retry || false}) }}",300)
    check=condition('Delivery succeeded?',650)
    make('email_approval','LeadReviveApproval','LeadRevive W3 - Approved outbox, safe retry and Mailpit',
        [schedule,webhook,dispatch,check,done,error],[(schedule['name'],dispatch['name'],0),(webhook['name'],dispatch['name'],0),
         (dispatch['name'],check['name'],0),(check['name'],done['name'],0),(check['name'],error['name'],1)])
    webhook=hook('status-sync')
    sync=http('Validate version and synchronize lead status','status-sync',"={{ JSON.stringify({...$json.body,execution_id:$execution.id}) }}",300)
    check=condition('Status synchronized?',650)
    make('status_sync','LeadReviveStatus','LeadRevive - Versioned lead status synchronization',
        [webhook,sync,check,done,error],[(webhook['name'],sync['name'],0),(sync['name'],check['name'],0),
         (check['name'],done['name'],0),(check['name'],error['name'],1)])
    print('Four credential-free original workflow exports written.')


if __name__=='__main__':main()
