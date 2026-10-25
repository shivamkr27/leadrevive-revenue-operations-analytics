# Verify the actual source slicer, then leave the report unfiltered.
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
& "$PSScriptRoot/powerbi_desktop.ps1" -Action Select -Value '03 Source performance | SYNTHETIC'
Add-Type -AssemblyName UIAutomationClient
$task=Get-Process PBIDesktop | Where-Object MainWindowTitle -like '*LeadRevive_Phase4*' | Sort-Object StartTime -Descending | Select-Object -First 1
$root=[System.Windows.Automation.AutomationElement]::FromHandle($task.MainWindowHandle)
function Assert-Card([int]$Expected){
 for($attempt=0;$attempt -lt 5;$attempt++){
  $controls=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  if($controls | Where-Object {$_.Current.Name -eq "KPI Lead count $Expected."}){return}
  Start-Sleep -Milliseconds 500
 }
 throw "Power BI visual did not show expected count $Expected"
}
$snapshot=Get-Content -Raw -Encoding UTF8 (Join-Path $taskRoot 'analytics/exports/snapshot.json') | ConvertFrom-Json
$expected=($snapshot.sources | Where-Object segment -eq 'Event').leads
Assert-Card $snapshot.kpis.new_leads
$item=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition) | Where-Object {$_.Current.Name -eq 'Event' -and $_.Current.ClassName -eq 'slicerItemContainer'} | Select-Object -First 1
($item.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)).Toggle()
Assert-Card $expected
& "$PSScriptRoot/powerbi_desktop.ps1" -Action Capture -Value (Join-Path $taskRoot 'screenshots/SS09i_PowerBI_Source_Filtered.png')
& "$PSScriptRoot/powerbi_desktop.ps1" -Action Invoke -Value 'Clear selections'
Assert-Card $snapshot.kpis.new_leads
@{result='passed';source='Event';filtered_visual_count=$expected;cleared_visual_count=$snapshot.kpis.new_leads;snapshot_id=$snapshot.snapshot_id} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $taskRoot 'data/processed/phase4_powerbi_filter.json')
Write-Output "Power BI source slicer verified: $expected; cleared $($snapshot.kpis.new_leads)."
