# Ralph Loop - Watermark removal (texture_synthesis, no blur)
# Usage: .\src\tools\ralph_clean.ps1 -Image assets/dirty/photo.jpg
#        .\src\tools\ralph_clean.ps1 -Image assets/dirty/photo.jpg -Output assets/clean/photo_ralph.png

param(
    [Parameter(Mandatory = $true)]
    [string]$Image,
    [string]$Output = "",
    [int]$MaxIterations = 6,
    [double]$CleanThreshold = 0.3
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

$imagePath = $Image
if (-not [System.IO.Path]::IsPathRooted($Image)) {
    $imagePath = Join-Path $projectRoot $Image
}
if (-not (Test-Path $imagePath)) {
    Write-Error "Image not found: $imagePath"
    exit 1
}
$imagePath = (Resolve-Path $imagePath).Path

Push-Location $projectRoot
try {
    $rlphArgs = @("ralph", $imagePath)
    if ($Output) {
        $outPath = $Output
        if (-not [System.IO.Path]::IsPathRooted($Output)) {
            $outPath = Join-Path $projectRoot $Output
        }
        $rlphArgs += "-o", $outPath
    }
    $rlphArgs += "--max-iterations", $MaxIterations
    $rlphArgs += "--clean-threshold", $CleanThreshold

    python -m stega.cli @rlphArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
