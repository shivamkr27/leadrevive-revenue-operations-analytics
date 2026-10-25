# Optional installed-Office review rendering. Opens only our generated documents.
param([switch]$WithWord)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$metadata=Get-Content -Raw -Encoding UTF8 (Join-Path $taskRoot 'data/processed/phase5_review_report.json') | ConvertFrom-Json
$folder=Join-Path (Join-Path $taskRoot 'reports/generated') $metadata.report_id
$preview=Join-Path (Join-Path $taskRoot 'reports/previews') $metadata.report_id
New-Item -ItemType Directory -Force -Path $preview | Out-Null
$hadPowerPoint=@(Get-Process POWERPNT -ErrorAction SilentlyContinue).Count -gt 0
$powerPoint=New-Object -ComObject PowerPoint.Application
try {
 $presentation=$powerPoint.Presentations.Open((Join-Path $folder 'LeadRevive_Management_SYNTHETIC.pptx'),$true,$false,$false)
 try {
  $presentation.Export($preview,'PNG',1600,900)
  $presentation.SaveAs((Join-Path $preview 'Management_Office_Preview.pdf'),32)
 } finally {$presentation.Close()}
} finally {if(-not $hadPowerPoint){$powerPoint.Quit()}}
Copy-Item -LiteralPath (Join-Path $preview 'Slide5.PNG') -Destination (Join-Path $taskRoot 'screenshots/SS12_Management_Presentation.png')
Write-Output 'PowerPoint opened successfully; actual slide and PDF previews exported.'
if(-not $WithWord){exit 0}
$word=New-Object -ComObject Word.Application
$word.Visible=$false;$word.DisplayAlerts=0
try {
 $document=$word.Documents.Open((Join-Path $folder 'LeadRevive_Report_SYNTHETIC.docx'),$false,$true)
 try {$document.ExportAsFixedFormat((Join-Path $preview 'Report_Office_Preview.pdf'),17)} finally {$document.Close($false)}
} finally {if($word.Documents.Count -eq 0){$word.Quit()}}
Write-Output 'Optional Word PDF preview exported.'
