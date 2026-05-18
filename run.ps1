param(
    [ValidateSet("run", "build", "ui", "quick")]
    [string]$Mode = "run",

    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",

    [switch]$Rebuild,

    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
$BuildDir = Join-Path $ProjectRoot "build_local"

function Write-Step {
    param([string]$Text)
    Write-Host "`n=== $Text ===" -ForegroundColor Cyan
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

function Resolve-SolverPath {
    param([string]$Config)

    $candidates = @(
        (Join-Path $BuildDir "$Config\poisson_solver.exe"),
        (Join-Path $BuildDir "poisson_solver.exe"),
        (Join-Path $BuildDir "poisson_solver"),
        (Join-Path $ProjectRoot "build\$Config\poisson_solver.exe"),
        (Join-Path $ProjectRoot "build\poisson_solver.exe")
    )

    foreach ($path in $candidates) {
        if (Test-Path $path) {
            return $path
        }
    }

    return $candidates[0]
}

function Ensure-Build {
    param([string]$Config, [bool]$DoRebuild)

    Write-Step "CMake configure"
    Invoke-Native { cmake -S . -B $BuildDir }

    Write-Step "CMake build ($Config)"
    if ($DoRebuild) {
        Invoke-Native { cmake --build $BuildDir --config $Config --clean-first }
    }
    else {
        Invoke-Native { cmake --build $BuildDir --config $Config }
    }
}

function Run-Solver {
    param(
        [string]$Solver,
        [string]$InputJson,
        [string]$OutDir
    )

    if (-not (Test-Path $InputJson)) {
        throw "Input JSON not found: $InputJson"
    }

    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    Write-Step "Run solver: $(Split-Path -Leaf $InputJson) -> $OutDir"
    Invoke-Native { & $Solver $InputJson $OutDir }
}

$needBuild = $Mode -in @("run", "build", "quick")
if ($needBuild) {
    Ensure-Build -Config $Configuration -DoRebuild:$Rebuild
}

$solverPath = Resolve-SolverPath -Config $Configuration
if (($Mode -in @("run", "quick")) -and -not (Test-Path $solverPath)) {
    throw "Solver executable not found: $solverPath"
}

switch ($Mode) {
    "build" {
        Write-Host "Build completed." -ForegroundColor Green
    }
    "run" {
        $input = Join-Path $ProjectRoot "input_examples\default_input.json"
        $out = if ($OutputDir) { $OutputDir } else { Join-Path $ProjectRoot "output" }
        Run-Solver -Solver $solverPath -InputJson $input -OutDir $out
    }
    "quick" {
        $input = Join-Path $ProjectRoot "input_examples\quick_input.json"
        $out = if ($OutputDir) { $OutputDir } else { Join-Path $ProjectRoot "output_quick" }
        Run-Solver -Solver $solverPath -InputJson $input -OutDir $out
    }
    "ui" {
        Write-Step "Install UI dependencies"
        Invoke-Native { python -m pip install -r (Join-Path $ProjectRoot "ui\requirements.txt") }

        Write-Step "Run UI"
        Invoke-Native { python (Join-Path $ProjectRoot "ui\app.py") }
    }
}

Write-Host "`nDone." -ForegroundColor Green
