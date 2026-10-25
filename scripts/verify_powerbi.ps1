# Query the actual Power BI Desktop Analysis Services model. No service account needed.
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
[System.Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.AdomdClient.dll') | Out-Null
$portFile=Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces" -Recurse -Filter msmdsrv.port.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $portFile){throw 'Open and refresh LeadRevive.pbip in Desktop first.'}
$port=[IO.File]::ReadAllText($portFile.FullName,[Text.Encoding]::Unicode).Trim()
$connection=New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$port")
$connection.Open()
try {
 $command=$connection.CreateCommand()
 $command.CommandText=@'
EVALUATE ROW(
 "snapshot_id",CALCULATE(SELECTEDVALUE(Snapshot[value]),Snapshot[field]="snapshot_id"),
 "data_revision",CALCULATE(SELECTEDVALUE(Snapshot[value]),Snapshot[field]="data_revision"),
 "model_sha256",CALCULATE(SELECTEDVALUE(Snapshot[value]),Snapshot[field]="model_sha256"),
 "new_leads",[KPI Lead count],"contacted",[KPI Contacted],"uncontacted",[KPI Uncontacted],
 "won",[KPI Won],"qualified",[KPI Qualified],"active_scheduled",[KPI Scheduled],
 "overdue",[KPI Overdue],"first_response_coverage",[KPI Response coverage],
 "qualified_rate",[KPI Qualified rate],"win_rate",[KPI Win rate],
 "overdue_rate",[KPI Overdue rate],"median_first_response_hours",[KPI Median response hours],
 "pipeline_exposure_inr",[KPI Pipeline exposure INR])
'@
 $reader=$command.ExecuteReader()
 if(-not $reader.Read()){throw 'No DAX result'}
 $values=@{}
 for($i=0;$i -lt $reader.FieldCount;$i++){
   $key=$reader.GetName($i).Trim('[',']')
   $values[$key]=if($reader.IsDBNull($i)){$null}else{$reader.GetValue($i)}
 }
 $reader.Close()
 $exportRoot=Join-Path $taskRoot 'analytics/exports'
 $pointer=Get-Content -Raw (Join-Path $exportRoot 'current.json') | ConvertFrom-Json
 $snapshot=Get-Content -Raw -Encoding UTF8 (Join-Path $exportRoot ('generations/'+$pointer.generation_id+'/snapshot.json')) | ConvertFrom-Json
 if($snapshot.snapshot_id -ne $values.snapshot_id){throw 'Power BI is on a different snapshot. Refresh Desktop.'}
 if($snapshot.data_revision -ne $values.data_revision -or $snapshot.provenance.model_sha256 -ne $values.model_sha256){throw 'Power BI model/data provenance mismatch.'}
 foreach($property in $snapshot.kpis.PSObject.Properties){
   $expectedNull=$null -eq $property.Value; $actualNull=$null -eq $values[$property.Name]
   if($expectedNull -ne $actualNull){throw "DAX null mismatch: $($property.Name)"}
   if(-not $expectedNull -and [math]::Abs([double]$property.Value-[double]$values[$property.Name]) -gt 0.00000001){throw "DAX mismatch: $($property.Name)"}
 }
 $result=@{result='passed';snapshot_id=$values.snapshot_id;data_revision=$values.data_revision;model_sha256=$values.model_sha256;verified_at_utc=[DateTime]::UtcNow.ToString('o');method='DAX query against actual Power BI Desktop model';values=$values}
 $result | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $taskRoot 'data/processed/phase4_powerbi.json')
 Write-Output "Power BI: all 13 DAX KPIs reconcile; snapshot $($values.snapshot_id)."
} finally {$connection.Close()}
