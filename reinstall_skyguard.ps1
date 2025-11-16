#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Reinstall SkyGuard from GitHub - Complete uninstall and fresh install
    
.DESCRIPTION
    This script will:
    1. Stop all running SkyGuard processes
    2. Uninstall Windows services (if any)
    3. Remove the SkyGuard directory
    4. Clone the GitHub repository
    5. Run the installation
    6. Start SkyGuard services
    
.PARAMETER SkyGuardPath
    Path where SkyGuard should be installed (default: parent of script location)
    
.PARAMETER GitHubRepo
    GitHub repository URL (default: https://github.com/jad3tx/SkyGuard.git)
    
.PARAMETER Branch
    Branch to clone (default: main)
    
.EXAMPLE
    .\reinstall_skyguard.ps1
    
.EXAMPLE
    .\reinstall_skyguard.ps1 -SkyGuardPath "C:\Projects\SkyGuard"
#>

param(
    [string]$SkyGuardPath = "",
    [string]$GitHubRepo = "https://github.com/jad3tx/SkyGuard.git",
    [string]$Branch = "main",
    [switch]$SkipBackup,
    [switch]$Force
)

# Error handling
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Error { Write-ColorOutput Red $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Info { Write-ColorOutput Cyan $args }

# Determine SkyGuard path
if ([string]::IsNullOrEmpty($SkyGuardPath)) {
    $ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $SkyGuardPath = Split-Path -Parent $ScriptPath
    if ($ScriptPath -like "*\SkyGuard\*") {
        $SkyGuardPath = $ScriptPath
    }
}

$SkyGuardPath = [System.IO.Path]::GetFullPath($SkyGuardPath)
Write-Info "SkyGuard path: $SkyGuardPath"

# Step 1: Stop all SkyGuard processes
Write-Info "`n🛑 Step 1: Stopping all SkyGuard processes..."
try {
    $processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $cmdline = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdline -like "*skyguard*"
    }
    
    if ($processes) {
        Write-Info "   Found $($processes.Count) SkyGuard process(es)"
        foreach ($proc in $processes) {
            Write-Info "   Stopping process PID: $($proc.Id)"
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
        Write-Success "   ✅ All processes stopped"
    } else {
        Write-Info "   No running SkyGuard processes found"
    }
} catch {
    Write-Warning "   ⚠️  Error stopping processes: $_"
}

# Step 2: Uninstall Windows services (if they exist)
Write-Info "`n🔧 Step 2: Checking for Windows services..."
try {
    $services = @("skyguard", "skyguard-web")
    foreach ($serviceName in $services) {
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($service) {
            Write-Info "   Found service: $serviceName"
            if ($service.Status -eq 'Running') {
                Write-Info "   Stopping service: $serviceName"
                Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
            }
            Write-Info "   Removing service: $serviceName"
            # Note: Service removal requires admin rights and sc.exe
            $result = sc.exe delete $serviceName 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "   ✅ Service $serviceName removed"
            } else {
                Write-Warning "   ⚠️  Could not remove service $serviceName (may require admin)"
            }
        }
    }
} catch {
    Write-Warning "   ⚠️  Error checking services: $_"
}

# Step 3: Backup configuration (optional)
if (-not $SkipBackup -and (Test-Path $SkyGuardPath)) {
    Write-Info "`n💾 Step 3: Creating backup of configuration..."
    try {
        $backupPath = "$SkyGuardPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        $configPath = Join-Path $SkyGuardPath "config"
        $modelsPath = Join-Path $SkyGuardPath "models"
        
        if (Test-Path $configPath) {
            New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
            Copy-Item -Path $configPath -Destination (Join-Path $backupPath "config") -Recurse -Force -ErrorAction SilentlyContinue
            Write-Success "   ✅ Configuration backed up to: $backupPath"
        }
        
        if (Test-Path $modelsPath) {
            if (-not (Test-Path $backupPath)) {
                New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
            }
            Copy-Item -Path $modelsPath -Destination (Join-Path $backupPath "models") -Recurse -Force -ErrorAction SilentlyContinue
            Write-Success "   ✅ Models backed up to: $backupPath"
        }
    } catch {
        Write-Warning "   ⚠️  Error creating backup: $_"
    }
}

# Step 4: Remove SkyGuard directory
Write-Info "`n🗑️  Step 4: Removing SkyGuard directory..."
if (Test-Path $SkyGuardPath) {
    if ($Force -or (Read-Host "   Remove directory '$SkyGuardPath'? (y/N)") -eq 'y') {
        try {
            Write-Info "   Removing: $SkyGuardPath"
            Remove-Item -Path $SkyGuardPath -Recurse -Force -ErrorAction Stop
            Start-Sleep -Seconds 1
            Write-Success "   ✅ Directory removed"
        } catch {
            Write-Error "   ❌ Error removing directory: $_"
            Write-Error "   Please remove it manually and run the script again"
            exit 1
        }
    } else {
        Write-Warning "   ⚠️  Skipping directory removal"
        exit 0
    }
} else {
    Write-Info "   Directory does not exist, skipping removal"
}

# Step 5: Clone GitHub repository
Write-Info "`n📥 Step 5: Cloning GitHub repository..."
try {
    $parentPath = Split-Path -Parent $SkyGuardPath
    if (-not (Test-Path $parentPath)) {
        New-Item -ItemType Directory -Path $parentPath -Force | Out-Null
    }
    
    Write-Info "   Repository: $GitHubRepo"
    Write-Info "   Branch: $Branch"
    Write-Info "   Destination: $SkyGuardPath"
    
    # Check if git is available
    $gitVersion = git --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "   ❌ Git is not installed or not in PATH"
        Write-Error "   Please install Git from https://git-scm.com/download/win"
        exit 1
    }
    
    Write-Info "   Cloning repository..."
    Push-Location $parentPath
    git clone -b $Branch $GitHubRepo $SkyGuardPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "   ❌ Failed to clone repository"
        exit 1
    }
    Pop-Location
    
    Write-Success "   ✅ Repository cloned successfully"
} catch {
    Write-Error "   ❌ Error cloning repository: $_"
    exit 1
}

# Step 6: Run installation
Write-Info "`n📦 Step 6: Running installation..."
try {
    Push-Location $SkyGuardPath
    
    # Check for uv (recommended package manager)
    $hasUv = Get-Command uv -ErrorAction SilentlyContinue
    if ($hasUv) {
        Write-Info "   Using uv for installation..."
        Write-Info "   Creating virtual environment..."
        uv venv
        
        Write-Info "   Installing dependencies..."
        uv pip install -r requirements.txt
        
        Write-Success "   ✅ Installation complete with uv"
    } else {
        Write-Info "   Using pip for installation..."
        
        # Check for Python
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) {
            Write-Error "   ❌ Python is not installed or not in PATH"
            Write-Error "   Please install Python from https://www.python.org/downloads/"
            exit 1
        }
        
        Write-Info "   Creating virtual environment..."
        python -m venv venv
        
        Write-Info "   Activating virtual environment..."
        & "$SkyGuardPath\venv\Scripts\Activate.ps1"
        
        Write-Info "   Upgrading pip..."
        python -m pip install --upgrade pip
        
        Write-Info "   Installing dependencies..."
        pip install -r requirements.txt
        
        Write-Success "   ✅ Installation complete with pip"
    }
    
    # Create necessary directories
    Write-Info "   Creating necessary directories..."
    @("logs", "data\detections", "models", "data\bird_species") | ForEach-Object {
        $dir = Join-Path $SkyGuardPath $_
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Pop-Location
} catch {
    Write-Error "   ❌ Error during installation: $_"
    Pop-Location
    exit 1
}

# Step 7: Restore configuration backup (if available)
if (-not $SkipBackup) {
    Write-Info "`n📋 Step 7: Restoring configuration backup..."
    $backupDirs = Get-ChildItem -Path (Split-Path -Parent $SkyGuardPath) -Filter "SkyGuard.backup.*" -Directory -ErrorAction SilentlyContinue | 
        Sort-Object LastWriteTime -Descending | 
        Select-Object -First 1
    
    if ($backupDirs) {
        $backupPath = $backupDirs.FullName
        Write-Info "   Found backup: $backupPath"
        
        $configBackup = Join-Path $backupPath "config"
        $modelsBackup = Join-Path $backupPath "models"
        
        if (Test-Path $configBackup) {
            Write-Info "   Restoring configuration..."
            Copy-Item -Path "$configBackup\*" -Destination (Join-Path $SkyGuardPath "config") -Recurse -Force -ErrorAction SilentlyContinue
            Write-Success "   ✅ Configuration restored"
        }
        
        if (Test-Path $modelsBackup) {
            Write-Info "   Restoring models..."
            Copy-Item -Path "$modelsBackup\*" -Destination (Join-Path $SkyGuardPath "models") -Recurse -Force -ErrorAction SilentlyContinue
            Write-Success "   ✅ Models restored"
        }
    } else {
        Write-Info "   No backup found, skipping restore"
    }
}

# Step 8: Start SkyGuard services
Write-Info "`n🚀 Step 8: Starting SkyGuard services..."
try {
    Push-Location $SkyGuardPath
    
    # Activate virtual environment
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
    }
    
    # Start main system
    Write-Info "   Starting main detection system..."
    $mainProcess = Start-Process -FilePath "python" -ArgumentList "-m", "skyguard.main" -WorkingDirectory $SkyGuardPath -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
    if ($mainProcess.HasExited -and $mainProcess.ExitCode -ne 0) {
        Write-Warning "   ⚠️  Main system may have failed to start (check logs)"
    } else {
        Write-Success "   ✅ Main system started (PID: $($mainProcess.Id))"
    }
    
    # Start web portal
    Write-Info "   Starting web portal..."
    $webProcess = Start-Process -FilePath "python" -ArgumentList "skyguard\web\app.py" -WorkingDirectory $SkyGuardPath -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
    if ($webProcess.HasExited -and $webProcess.ExitCode -ne 0) {
        Write-Warning "   ⚠️  Web portal may have failed to start (check logs)"
    } else {
        Write-Success "   ✅ Web portal started (PID: $($webProcess.Id))"
    }
    
    Pop-Location
} catch {
    Write-Error "   ❌ Error starting services: $_"
    Pop-Location
    exit 1
}

# Final summary
Write-Success "`n✅ SkyGuard reinstallation complete!"
Write-Info "`n📋 Summary:"
Write-Info "   - SkyGuard path: $SkyGuardPath"
Write-Info "   - Main system: http://localhost:8080 (if web portal started)"
Write-Info "   - Logs: $SkyGuardPath\logs"
Write-Info "`n💡 Next steps:"
Write-Info "   1. Check logs in: $SkyGuardPath\logs"
Write-Info "   2. Access web portal at: http://localhost:8080"
Write-Info "   3. Configure system in: $SkyGuardPath\config\skyguard.yaml"

