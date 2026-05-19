# Cursor Agent Headless - Watermark Removal Pipeline
# Requires: Cursor Pro, agent CLI installed, CURSOR_API_KEY set (or agent auth)
# Usage: .\src\tools\cursor_agent_clean.ps1 -Image <path_to_image>
#        .\src\tools\cursor_agent_clean.ps1 -Image assets/dirty/photo.jpg

param(
    [Parameter(Mandatory = $true)]
    [string]$Image,
    [string]$Output = "",
    [switch]$NoForce
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

# Resolve image path
$imagePath = $Image
if (-not [System.IO.Path]::IsPathRooted($Image)) {
    $imagePath = Join-Path $projectRoot $Image
}
if (-not (Test-Path $imagePath)) {
    Write-Error "Image not found: $imagePath"
    exit 1
}
$imagePath = (Resolve-Path $imagePath).Path

# Build prompt from template
$promptFile = Join-Path $scriptDir "prompts\agentic_watermark_removal.txt"
$prompt = (Get-Content $promptFile -Raw) -replace '\{\{IMAGE_PATH\}\}', $imagePath

# Write to temp file (avoids escaping issues with long paths)
$tempPrompt = [System.IO.Path]::GetTempFileName()
$prompt | Out-File -FilePath $tempPrompt -Encoding utf8

# Change to project root
Push-Location $projectRoot

try {
    $forceFlag = if ($NoForce) { "" } else { "--force" }
    $promptContent = Get-Content $tempPrompt -Raw
    $args = @("-p", $promptContent, "--output-format", "text")
    if ($forceFlag) { $args += $forceFlag }
    Write-Host "Running Cursor agent on: $imagePath"
    & agent @args
}
finally {
    Pop-Location
    Remove-Item $tempPrompt -ErrorAction SilentlyContinue
}
exit $LASTEXITCODE
