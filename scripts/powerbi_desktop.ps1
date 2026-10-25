param([ValidateSet('Inspect','Invoke','Capture','Select')][string]$Action='Inspect',[string]$Value='', [string]$Title='LeadRevive')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class LeadReviveDesktop {
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h,IntPtr dc,uint f);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT r);
 public struct RECT { public int Left,Top,Right,Bottom; }
}
'@
$pbiTask=Get-Process PBIDesktop | Where-Object {$_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$Title*"} | Sort-Object StartTime -Descending | Select-Object -First 1
if(-not $pbiTask){Get-Process PBIDesktop | Select-Object Id,MainWindowTitle; exit 1}
$pbiRoot=[System.Windows.Automation.AutomationElement]::FromHandle($pbiTask.MainWindowHandle)
if($Action -eq 'Inspect'){
 $pbiRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition) | Where-Object {$_.Current.Name -ne ''} | ForEach-Object {$_.Current.ControlType.ProgrammaticName+' | '+$_.Current.Name}
} elseif($Action -eq 'Select'){
 $match=$pbiRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition) | Where-Object {$_.Current.Name -eq $Value -and $_.Current.IsEnabled -and $_.GetSupportedPatterns().Id -contains [System.Windows.Automation.SelectionItemPattern]::Pattern.Id} | Select-Object -First 1
 if(-not $match){throw "Selectable control not found: $Value"}
 ($match.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
} elseif($Action -eq 'Invoke'){
 $match=$pbiRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition) | Where-Object {$_.Current.Name -eq $Value -and $_.Current.IsEnabled -and -not $_.Current.IsOffscreen -and $_.GetSupportedPatterns().Id -contains [System.Windows.Automation.InvokePattern]::Pattern.Id} | Select-Object -First 1
 if(-not $match){throw "Control not found: $Value"}
 ($match.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)).Invoke()
} else {
 $rect=New-Object LeadReviveDesktop+RECT
 [LeadReviveDesktop]::GetWindowRect($pbiTask.MainWindowHandle,[ref]$rect) | Out-Null
 $bitmap=New-Object System.Drawing.Bitmap(($rect.Right-$rect.Left),($rect.Bottom-$rect.Top))
 $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
 $dc=$graphics.GetHdc()
 $captured=[LeadReviveDesktop]::PrintWindow($pbiTask.MainWindowHandle,$dc,2)
 $graphics.ReleaseHdc($dc)
 if(-not $captured){throw 'Power BI window capture failed.'}
 $bitmap.Save($Value,[System.Drawing.Imaging.ImageFormat]::Png)
 $graphics.Dispose();$bitmap.Dispose()
}
