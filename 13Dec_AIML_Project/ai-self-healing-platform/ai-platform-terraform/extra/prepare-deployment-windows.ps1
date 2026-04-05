# prepare-deployment-complete.ps1
# Prepares your COMPLETE AI platform project for Terraform deployment
# Windows PowerShell Compatible Version

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "."
)

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  AI Platform - Preparing COMPLETE Project for Deployment" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "Source Project: $ProjectPath" -ForegroundColor Yellow
Write-Host ""

# Verify source path exists
if (-not (Test-Path $ProjectPath)) {
    Write-Host "ERROR: Project path not found: $ProjectPath" -ForegroundColor Red
    exit 1
}

# Create app-files directory structure
Write-Host "Creating app-files directory..." -ForegroundColor Yellow
Remove-Item -Path "app-files" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "app-files" | Out-Null
New-Item -ItemType Directory -Force -Path "app-files/kubernetes" | Out-Null

# ============================================================================
# COPY ENTIRE SRC DIRECTORY (ALL SUBDIRECTORIES)
# ============================================================================

Write-Host "`nCopying ENTIRE src/ directory with ALL subdirectories..." -ForegroundColor Yellow

if (Test-Path "$ProjectPath/src") {
    # Copy entire src folder recursively
    Copy-Item "$ProjectPath/src" "app-files/" -Recurse -Force
    
    # Count what we copied
    $fileCount = (Get-ChildItem "app-files/src" -Recurse -File).Count
    $dirCount = (Get-ChildItem "app-files/src" -Recurse -Directory).Count
    
    Write-Host "  SUCCESS: Copied src/ directory" -ForegroundColor Green
    Write-Host "     - $dirCount subdirectories" -ForegroundColor Gray
    Write-Host "     - $fileCount files" -ForegroundColor Gray
    
    # List subdirectories copied
    Write-Host "`n  Subdirectories copied:" -ForegroundColor Cyan
    Get-ChildItem "app-files/src" -Directory -Recurse | ForEach-Object {
        $relativePath = $_.FullName -replace [regex]::Escape((Get-Item "app-files/src").FullName), ""
        Write-Host "     OK: src$relativePath" -ForegroundColor Gray
    }
} else {
    Write-Host "  ERROR: src/ directory not found in $ProjectPath" -ForegroundColor Red
    exit 1
}

# ============================================================================
# COPY DOCKERFILES
# ============================================================================

Write-Host "`nCopying Dockerfiles..." -ForegroundColor Yellow

$dockerfiles = @("Dockerfile", "Dockerfile.platform", "Dockerfile.sampleapp")
foreach ($dockerfile in $dockerfiles) {
    if (Test-Path "$ProjectPath/$dockerfile") {
        Copy-Item "$ProjectPath/$dockerfile" "app-files/" -Force
        Write-Host "  SUCCESS: Copied $dockerfile" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: $dockerfile not found (will use default)" -ForegroundColor Yellow
    }
}

# ============================================================================
# COPY REQUIREMENTS
# ============================================================================

Write-Host "`nCopying requirements..." -ForegroundColor Yellow

if (Test-Path "$ProjectPath/requirements.txt") {
    Copy-Item "$ProjectPath/requirements.txt" "app-files/" -Force
    Write-Host "  SUCCESS: Copied requirements.txt" -ForegroundColor Green
} else {
    Write-Host "  WARNING: requirements.txt not found" -ForegroundColor Yellow
}

# ============================================================================
# COPY KUBERNETES MANIFESTS
# ============================================================================

Write-Host "`nCopying Kubernetes manifests..." -ForegroundColor Yellow

$k8sFiles = @("ai-platform.yaml", "sample-app.yaml", "kubernetes-sample.yaml")
$copiedCount = 0

foreach ($file in $k8sFiles) {
    if (Test-Path "$ProjectPath/kubernetes/$file") {
        Copy-Item "$ProjectPath/$file" "app-files/kubernetes/" -Force
        Write-Host "  SUCCESS: Copied $file" -ForegroundColor Green
        $copiedCount++
    }
}

if ($copiedCount -eq 0) {
    Write-Host "  WARNING: No Kubernetes manifests found (will use defaults)" -ForegroundColor Yellow
}

# ============================================================================
# COPY SAMPLE APP (if exists)
# ============================================================================

Write-Host "`nCopying sample app..." -ForegroundColor Yellow

if (Test-Path "$ProjectPath/sample_app.py") {
    Copy-Item "$ProjectPath/sample_app.py" "app-files/" -Force
    Write-Host "  SUCCESS: Copied sample_app.py" -ForegroundColor Green
} else {
    Write-Host "  WARNING: sample_app.py not found (will use default)" -ForegroundColor Yellow
}

# ============================================================================
# COPY ADDITIONAL FILES (if needed)
# ============================================================================

Write-Host "`nCopying additional files..." -ForegroundColor Yellow

$additionalFiles = @(
    "config.yaml",
    "config.json",
    ".env.example",
    "setup.py"
)

$additionalCopied = 0
foreach ($file in $additionalFiles) {
    if (Test-Path "$ProjectPath/$file") {
        Copy-Item "$ProjectPath/$file" "app-files/" -Force
        Write-Host "  SUCCESS: Copied $file" -ForegroundColor Green
        $additionalCopied++
    }
}

if ($additionalCopied -eq 0) {
    Write-Host "  No additional config files found" -ForegroundColor Gray
}

# ============================================================================
# CREATE DEPLOYMENT MANIFEST
# ============================================================================

Write-Host "`nCreating deployment manifest..." -ForegroundColor Yellow

$manifest = @"
================================================================
AI SELF-HEALING PLATFORM - DEPLOYMENT MANIFEST
================================================================

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Source: $ProjectPath
Target: app-files/

================================================================
FILES COPIED TO app-files/
================================================================

"@

# Get all files recursively
$allFiles = Get-ChildItem -Path "app-files" -Recurse -File
$manifest += "`nTotal Files: $($allFiles.Count)`n"
$manifest += "Total Size: $([math]::Round(($allFiles | Measure-Object -Property Length -Sum).Sum / 1MB, 2)) MB`n`n"

# Group by directory
$manifest += "Directory Structure:`n"
$manifest += "----------------------------------------------------------------`n"

Get-ChildItem -Path "app-files" -Recurse -Directory | Sort-Object FullName | ForEach-Object {
    $relativePath = $_.FullName -replace [regex]::Escape($PWD.Path + "\app-files"), ""
    $fileCount = (Get-ChildItem $_.FullName -File).Count
    $manifest += "  Folder: .$relativePath ($fileCount files)`n"
}

$manifest += "`n"
$manifest += "Key Files:`n"
$manifest += "----------------------------------------------------------------`n"

# List important files
$importantFiles = @(
    "Dockerfile*",
    "requirements.txt",
    "*.yaml",
    "sample_app.py",
    "src/api/main*.py"
)

foreach ($pattern in $importantFiles) {
    Get-ChildItem -Path "app-files" -Recurse -File -Include $pattern | ForEach-Object {
        $relativePath = $_.FullName -replace [regex]::Escape($PWD.Path + "\app-files"), ""
        $size = [math]::Round($_.Length / 1KB, 1)
        $manifest += "  OK: .$relativePath ($size KB)`n"
    }
}

$manifest += "`n"
$manifest += "================================================================`n"
$manifest += "READY FOR DEPLOYMENT!`n"
$manifest += "================================================================`n"

$manifest | Out-File "app-files/DEPLOYMENT_MANIFEST.txt" -Encoding UTF8

# ============================================================================
# DISPLAY SUMMARY
# ============================================================================

Write-Host "`n================================================================" -ForegroundColor Green
Write-Host "  SUCCESS: PROJECT FILES PREPARED!" -ForegroundColor Green
Write-Host "================================================================`n" -ForegroundColor Green

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Total Files: $($allFiles.Count)" -ForegroundColor White
Write-Host "  Total Size: $([math]::Round(($allFiles | Measure-Object -Property Length -Sum).Sum / 1MB, 2)) MB" -ForegroundColor White
Write-Host ""

Write-Host "Directory Structure:" -ForegroundColor Cyan
Get-ChildItem -Path "app-files" -Directory | ForEach-Object {
    $fileCount = (Get-ChildItem $_.FullName -Recurse -File).Count
    Write-Host "  OK: $($_.Name)/ ($fileCount files)" -ForegroundColor Gray
}

Write-Host "`nFiles saved to:" -ForegroundColor Cyan
Write-Host "  $(Join-Path $PWD 'app-files')" -ForegroundColor White

Write-Host "`nManifest saved to:" -ForegroundColor Cyan
Write-Host "  $(Join-Path $PWD 'app-files\DEPLOYMENT_MANIFEST.txt')" -ForegroundColor White

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Review files in app-files/ directory" -ForegroundColor White
Write-Host "  2. Check DEPLOYMENT_MANIFEST.txt for details" -ForegroundColor White
Write-Host "  3. Run: terraform init" -ForegroundColor White
Write-Host "  4. Run: terraform apply" -ForegroundColor White
Write-Host ""

# Verify critical files
Write-Host "Verification:" -ForegroundColor Yellow
$criticalFiles = @(
    "app-files/src/api/main.py",
    "app-files/Dockerfile.platform",
    "app-files/kubernetes/ai-platform.yaml"
)

$allCriticalPresent = $true
foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "  SUCCESS: $($file -replace 'app-files/', '')" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $($file -replace 'app-files/', '')" -ForegroundColor Red
        $allCriticalPresent = $false
    }
}

if ($allCriticalPresent) {
    Write-Host "`nAll critical files present - Ready for deployment!" -ForegroundColor Green
} else {
    Write-Host "`nSome files missing - Check your source directory" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Run: .\verify-before-deploy.ps1 to verify everything" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
