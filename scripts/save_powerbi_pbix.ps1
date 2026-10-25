# Use only after Desktop File > Save as > Browse this device opens Save As.
# This acts on the Power BI dialog only and does not type into other apps.
param([string]$Name='LeadRevive_Phase4_SYNTHETIC.pbix')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type @'
using System; using System.Runtime.InteropServices;
public class LeadRevivePbixSave {
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h,uint m,IntPtr w,string l);
 [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 [DllImport("user32.dll")] public static extern IntPtr GetParent(IntPtr h);
}
'@
$taskRoot=Split-Path -Parent $PSScriptRoot
$path=Join-Path (Join-Path $taskRoot 'analytics/powerbi') $Name
if(Test-Path -LiteralPath $path){throw 'Target already exists. Use a new name or save within Desktop.'}
$task=Get-Process PBIDesktop | Where-Object MainWindowTitle -like '*LeadRevive*' | Sort-Object StartTime -Descending | Select-Object -First 1
$root=[System.Windows.Automation.AutomationElement]::FromHandle($task.MainWindowHandle)
$all=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$edit=$all | Where-Object {$_.Current.ClassName -eq 'Edit' -and $_.Current.AutomationId -eq '1001'} | Select-Object -First 1
$type=$all | Where-Object {$_.Current.AutomationId -eq 'FileTypeControlHost'} | Select-Object -First 1
$save=$all | Where-Object {$_.Current.ClassName -eq 'Button' -and $_.Current.AutomationId -eq '1'} | Select-Object -First 1
if(-not $edit -or -not $type -or -not $save){throw 'Power BI Save As dialog is required.'}
$eh=[IntPtr]$edit.Current.NativeWindowHandle
[LeadRevivePbixSave]::SendMessage($eh,12,[IntPtr]::Zero,'') | Out-Null
foreach($ch in $path.ToCharArray()){
 [LeadRevivePbixSave]::PostMessage($eh,258,[IntPtr][int][char]$ch,[IntPtr]::Zero) | Out-Null
}
$th=[IntPtr]$type.Current.NativeWindowHandle
[LeadRevivePbixSave]::SendMessage($th,334,[IntPtr]::Zero,[IntPtr]::Zero) | Out-Null
[LeadRevivePbixSave]::SendMessage([LeadRevivePbixSave]::GetParent($th),273,[IntPtr]589824,$th) | Out-Null
[LeadRevivePbixSave]::SendMessage([LeadRevivePbixSave]::GetParent($th),273,[IntPtr]65536,$th) | Out-Null
Start-Sleep -Milliseconds 500
[LeadRevivePbixSave]::PostMessage([IntPtr]$save.Current.NativeWindowHandle,245,[IntPtr]::Zero,[IntPtr]::Zero) | Out-Null
Write-Output 'PBIX save requested; verify file and reopen before claiming success.'
