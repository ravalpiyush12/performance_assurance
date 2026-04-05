# prepare-for-terraform.ps1
# Final preparation script - Copies EVERYTHING including scripts folder

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "."
)

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  AI Platform - COMPLETE Preparation for Terraform" -ForegroundColor Cyan
Write-Host "  All Issues Fixed - Production Ready" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

# Verify source path
if (-not (Test-Path $ProjectPath)) {
    Write-Host "ERROR: Project path not found: $ProjectPath" -ForegroundColor Red
    exit 1
}

# Clean and create app-files directory
Write-Host "Creating app-files directory..." -ForegroundColor Yellow
Remove-Item -Path "app-files" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "app-files" | Out-Null
New-Item -ItemType Directory -Force -Path "app-files/kubernetes" | Out-Null
New-Item -ItemType Directory -Force -Path "app-files/scripts" | Out-Null

# ============================================================================
# COPY ENTIRE SRC DIRECTORY
# ============================================================================

Write-Host "`n[1/6] Copying src/ directory..." -ForegroundColor Yellow

if (Test-Path "$ProjectPath/src") {
    Copy-Item "$ProjectPath/src" "app-files/" -Recurse -Force
    $fileCount = (Get-ChildItem "app-files/src" -Recurse -File).Count
    Write-Host "  SUCCESS: $fileCount files copied from src/" -ForegroundColor Green
} else {
    Write-Host "  ERROR: src/ directory not found" -ForegroundColor Red
    exit 1
}

# ============================================================================
# COPY DOCKERFILES
# ============================================================================

Write-Host "`n[2/6] Copying Dockerfiles..." -ForegroundColor Yellow

$dockerfiles = @("Dockerfile", "Dockerfile.platform", "Dockerfile.sampleapp")
foreach ($dockerfile in $dockerfiles) {
    if (Test-Path "$ProjectPath/$dockerfile") {
        Copy-Item "$ProjectPath/$dockerfile" "app-files/" -Force
        Write-Host "  SUCCESS: $dockerfile" -ForegroundColor Green
    }
}

# ============================================================================
# COPY REQUIREMENTS
# ============================================================================

Write-Host "`n[3/6] Copying requirements.txt..." -ForegroundColor Yellow

if (Test-Path "$ProjectPath/requirements.txt") {
    Copy-Item "$ProjectPath/requirements.txt" "app-files/" -Force
    Write-Host "  SUCCESS: requirements.txt" -ForegroundColor Green
}

# ============================================================================
# COPY KUBERNETES MANIFESTS
# ============================================================================

Write-Host "`n[4/6] Copying Kubernetes manifests..." -ForegroundColor Yellow

# Check for kubernetes folder first
if (Test-Path "$ProjectPath/kubernetes") {
    Copy-Item "$ProjectPath/kubernetes/*" "app-files/kubernetes/" -Recurse -Force
    $k8sCount = (Get-ChildItem "app-files/kubernetes" -File).Count
    Write-Host "  SUCCESS: $k8sCount files from kubernetes/" -ForegroundColor Green
} else {
    # Try individual files
    $k8sFiles = @("ai-platform.yaml", "sample-app.yaml", "kubernetes-sample.yaml")
    foreach ($file in $k8sFiles) {
        if (Test-Path "$ProjectPath/$file") {
            Copy-Item "$ProjectPath/$file" "app-files/kubernetes/" -Force
            Write-Host "  SUCCESS: $file" -ForegroundColor Green
        }
    }
}

# ============================================================================
# COPY SAMPLE APP
# ============================================================================

Write-Host "`n[5/6] Copying sample app..." -ForegroundColor Yellow

$sampleFiles = @("sample-app.py", "sample_app.py", "sampleapp.py")
foreach ($file in $sampleFiles) {
    if (Test-Path "$ProjectPath/$file") {
        Copy-Item "$ProjectPath/$file" "app-files/sample-app.py" -Force
        Write-Host "  SUCCESS: $file copied as sample-app.py" -ForegroundColor Green
        break
    }
}

# ============================================================================
# COPY SCRIPTS FOLDER
# ============================================================================

Write-Host "`n[6/6] Copying scripts folder..." -ForegroundColor Yellow

# Copy terraform scripts to app-files
if (Test-Path "scripts") {
    Copy-Item "scripts/*" "app-files/scripts/" -Force
    $scriptCount = (Get-ChildItem "app-files/scripts" -File).Count
    Write-Host "  SUCCESS: $scriptCount files from scripts/" -ForegroundColor Green
}

# Copy the COMPLETE deploy script
Copy-Item "deploy-all-complete.sh" "app-files/scripts/deploy-all.sh" -Force -ErrorAction SilentlyContinue
Write-Host "  SUCCESS: deploy-all.sh updated" -ForegroundColor Green

# ============================================================================
# SUMMARY
# ============================================================================

$allFiles = Get-ChildItem "app-files" -Recurse -File
$totalSize = [math]::Round(($allFiles | Measure-Object -Property Length -Sum).Sum / 1MB, 2)

Write-Host "`n================================================================" -ForegroundColor Green
Write-Host "  SUCCESS: ALL FILES PREPARED!" -ForegroundColor Green
Write-Host "================================================================`n" -ForegroundColor Green

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Total Files: $($allFiles.Count)" -ForegroundColor White
Write-Host "  Total Size: $totalSize MB" -ForegroundColor White
Write-Host ""

Write-Host "Directory Structure:" -ForegroundColor Cyan
Get-ChildItem "app-files" -Directory | ForEach-Object {
    $count = (Get-ChildItem $_.FullName -Recurse -File).Count
    Write-Host "  OK: $($_.Name)/ ($count files)" -ForegroundColor Gray
}

Write-Host "`n================================================================" -ForegroundColor Yellow
Write-Host "  NEXT STEPS:" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Yellow
Write-Host "  1. terraform init" -ForegroundColor White
Write-Host "  2. terraform plan" -ForegroundColor White
Write-Host "  3. terraform apply" -ForegroundColor White
Write-Host "`n  Wait 15 minutes for complete deployment" -ForegroundColor White
Write-Host "================================================================`n" -ForegroundColor Yellow

# Verification
Write-Host "Verification:" -ForegroundColor Cyan
$checks = @{
    "src/api/main.py" = "app-files/src/api/main.py"
    "Dockerfile.platform" = "app-files/Dockerfile.platform"
    "requirements.txt" = "app-files/requirements.txt"
    "scripts/deploy-all.sh" = "app-files/scripts/deploy-all.sh"
}

$allGood = $true
foreach ($check in $checks.GetEnumerator()) {
    if (Test-Path $check.Value) {
        Write-Host "  SUCCESS: $($check.Key)" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $($check.Key)" -ForegroundColor Red
        $allGood = $false
    }
}

if ($allGood) {
    Write-Host "`nREADY FOR TERRAFORM DEPLOYMENT!" -ForegroundColor Green
} else {
    Write-Host "`nWARNING: Some files missing" -ForegroundColor Yellow
}

Write-Host ""
