# Validate and PRINT the future origin command. Never changes Git configuration or pushes.
param([Parameter(Mandatory=$true)][string]$RepositoryUrl)
$ErrorActionPreference='Stop'
if ($RepositoryUrl -notmatch '^https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+\.git$') {
    throw 'Use an HTTPS GitHub repository URL ending in .git, with no credentials or query string.'
}
$projectRoot=Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $remoteNames=@(git remote)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect Git remotes; nothing changed.' }
    if ($remoteNames -contains 'origin') {
        $existingOrigin=git remote get-url origin
        if ($existingOrigin -eq $RepositoryUrl) {
            Write-Output 'Origin already matches. No command needed; no changes made.'
        } else {
            throw 'Origin exists with a different URL. Inspect it manually; nothing was overwritten.'
        }
    } else {
        Write-Output "Prepared command only: git remote add origin $RepositoryUrl"
    }
    Write-Output 'No remote configuration, commit, tag, publication or push performed.'
} finally { Pop-Location }
