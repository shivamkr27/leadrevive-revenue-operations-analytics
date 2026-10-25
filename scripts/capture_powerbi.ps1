# Capture only the report window; no desktop/foreground or global input access.
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System; using System.Runtime.InteropServices;
public class LeadReviveReportCapture {
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h,IntPtr dc,uint flags);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT rect);
 public struct RECT {public int Left,Top,Right,Bottom;}
}
'@
$taskRoot=Split-Path -Parent $PSScriptRoot
$task=Get-Process PBIDesktop | Where-Object MainWindowTitle -like '*LeadRevive_Phase4_SYNTHETIC*' | Sort-Object StartTime -Descending | Select-Object -First 1
if(-not $task){throw 'Open the final Phase 4 PBIX first.'}
$root=[System.Windows.Automation.AutomationElement]::FromHandle($task.MainWindowHandle)
$controls=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$tips=$controls | Where-Object {$_.Current.ClassName -eq 'close-btn'}
foreach($tip in $tips){try {($tip.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)).Invoke()}catch{}}
$pages=@(
 @('01 Funnel & stages | SYNTHETIC','SS09b_PowerBI_Funnel.png'),
 @('02 Follow-up exposure | SYNTHETIC','SS09_PowerBI_Analysis.png'),
 @('03 Source performance | SYNTHETIC','SS09c_PowerBI_Source.png'),
 @('04 Owner workload | SYNTHETIC','SS09d_PowerBI_Owners.png'),
 @('05 Response SLA | SYNTHETIC','SS09e_PowerBI_SLA.png'),
 @('06 Workflow evidence | SYNTHETIC','SS09f_PowerBI_Workflows.png'),
 @('07 Modeled comparison | SYNTHETIC','SS09g_PowerBI_Simulation.png'),
 @('08 KPI reconciliation | SYNTHETIC','SS09h_PowerBI_Reconciliation.png'))
$evidence=@()
foreach($page in $pages){
 $control=$controls | Where-Object {$_.Current.Name -eq $page[0] -and $_.GetSupportedPatterns().Id -contains [System.Windows.Automation.SelectionItemPattern]::Pattern.Id} | Select-Object -First 1
 if(-not $control){throw "Missing page: $($page[0])"}
 ($control.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
 Start-Sleep -Milliseconds 900
 $rect=New-Object LeadReviveReportCapture+RECT
 [LeadReviveReportCapture]::GetWindowRect($task.MainWindowHandle,[ref]$rect) | Out-Null
 $bitmap=New-Object Drawing.Bitmap(($rect.Right-$rect.Left),($rect.Bottom-$rect.Top))
 $graphics=[Drawing.Graphics]::FromImage($bitmap);$dc=$graphics.GetHdc()
 $ok=[LeadReviveReportCapture]::PrintWindow($task.MainWindowHandle,$dc,2)
 $graphics.ReleaseHdc($dc)
 if(-not $ok){throw 'Window capture failed.'}
 $bitmap.Save((Join-Path (Join-Path $taskRoot 'screenshots') $page[1]),[Drawing.Imaging.ImageFormat]::Png)
 $graphics.Dispose();$bitmap.Dispose()
 $evidence+=@{page=$page[0];screenshot=$page[1];capture='actual reopened PBIX window'}
}
$evidence | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $taskRoot 'data/processed/phase4_powerbi_pages.json')
Write-Output 'Captured all eight pages from the reopened PBIX.'
