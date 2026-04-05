# prepare-production-fixed.ps1
# Final preparation for single-node deployment

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  AI Platform - Production Preparation (Single Node)" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

$projectRoot = "G:\F Drive\Piyush Data\Learning\performance_assurance\13Dec_AIML_Project\ai-self-healing-platform"

# Clean and create directories
Write-Host "Cleaning up old files..." -ForegroundColor Yellow
Remove-Item -Path "app-files" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "app-files" | Out-Null
New-Item -ItemType Directory -Force -Path "app-files/kubernetes" | Out-Null
New-Item -ItemType Directory -Force -Path "app-files/scripts" | Out-Null

# ============================================================================
# STEP 1: Copy src directory
# ============================================================================
Write-Host "`n[1/6] Copying src/ directory..." -ForegroundColor Yellow
$srcPath = "$projectRoot\src"
if (Test-Path $srcPath) {
    Copy-Item $srcPath "app-files/" -Recurse -Force
    $srcFiles = (Get-ChildItem "app-files\src" -Recurse -File).Count
    Write-Host "  SUCCESS: $srcFiles files copied" -ForegroundColor Green
} else {
    Write-Host "  WARNING: src/ directory not found" -ForegroundColor Yellow
}

# ============================================================================
# STEP 2: Copy Dockerfiles and requirements
# ============================================================================
Write-Host "`n[2/6] Copying Dockerfiles and requirements..." -ForegroundColor Yellow

$filesToCopy = @(
    "Dockerfile.platform",
    "Dockerfile.sampleapp", 
    "Dockerfile",
    "requirements.txt"
)

foreach ($file in $filesToCopy) {
    if (Test-Path "$projectRoot\$file") {
        Copy-Item "$projectRoot\$file" "app-files/" -Force
        Write-Host "  OK: $file" -ForegroundColor Gray
    }
}
Write-Host "  SUCCESS" -ForegroundColor Green

# ============================================================================
# STEP 3: Copy Kubernetes manifests
# ============================================================================
Write-Host "`n[3/6] Copying Kubernetes manifests..." -ForegroundColor Yellow

if (Test-Path "$projectRoot\kubernetes") {
    Copy-Item "$projectRoot\kubernetes\*" "app-files\kubernetes\" -Force -ErrorAction SilentlyContinue
    $k8sFiles = (Get-ChildItem "app-files\kubernetes" -File).Count
    Write-Host "  SUCCESS: $k8sFiles manifest files" -ForegroundColor Green
} else {
    Write-Host "  WARNING: kubernetes/ directory not found" -ForegroundColor Yellow
}

# ============================================================================
# STEP 4: Copy sample app
# ============================================================================
Write-Host "`n[4/6] Copying sample app..." -ForegroundColor Yellow

$sampleFiles = @("sample-app.py", "sample_app.py", "sampleapp.py")
foreach ($file in $sampleFiles) {
    if (Test-Path "$projectRoot\$file") {
        Copy-Item "$projectRoot\$file" "app-files\sample-app.py" -Force
        Write-Host "  SUCCESS: $file copied as sample-app.py" -ForegroundColor Green
        break
    }
}

# ============================================================================
# STEP 5: Copy ALL scripts from terraform scripts folder
# ============================================================================
Write-Host "`n[5/6] Copying terraform scripts..." -ForegroundColor Yellow

# Check if scripts folder exists in terraform directory
if (Test-Path "scripts") {
    # Copy ALL files from terraform scripts folder
    Copy-Item "scripts\*" "app-files\scripts\" -Force
    $scriptFiles = (Get-ChildItem "app-files\scripts" -File).Count
    Write-Host "  SUCCESS: $scriptFiles script files copied" -ForegroundColor Green
    
    # List what was copied
    Get-ChildItem "app-files\scripts" -File | ForEach-Object {
        Write-Host "    - $($_.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "  WARNING: scripts/ folder not found in terraform directory" -ForegroundColor Yellow
}

# ============================================================================
# STEP 6: Copy the production deployment script
# ============================================================================
Write-Host "`n[6/6] Adding production deployment script..." -ForegroundColor Yellow

# Copy the production deployment script and rename it
if (Test-Path "deploy-all-production.sh") {
    Copy-Item "deploy-all-production.sh" "app-files\scripts\deploy-all.sh" -Force
    Write-Host "  SUCCESS: deploy-all.sh updated" -ForegroundColor Green
} else {
    Write-Host "  WARNING: deploy-all-production.sh not found" -ForegroundColor Yellow
    Write-Host "  Using existing scripts/deploy-all.sh if present" -ForegroundColor Yellow
}

# ============================================================================
# VERIFICATION
# ============================================================================
Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  VERIFICATION" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$checks = @{
    "src/" = "app-files\src"
    "Dockerfile.platform" = "app-files\Dockerfile.platform"
    "requirements.txt" = "app-files\requirements.txt"
    "scripts/deploy-all.sh" = "app-files\scripts\deploy-all.sh"
    "scripts/master-init.sh" = "app-files\scripts\master-init.sh"
}

$allGood = $true
foreach ($check in $checks.GetEnumerator()) {
    if (Test-Path $check.Value) {
        Write-Host "  OK: $($check.Key)" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $($check.Key)" -ForegroundColor Red
        $allGood = $false
    }
}

# Summary
$totalFiles = (Get-ChildItem "app-files" -Recurse -File).Count
$totalSize = [math]::Round(((Get-ChildItem "app-files" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB), 2)

Write-Host "`n================================================================" -ForegroundColor Green
Write-Host "  SUMMARY" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  Total Files: $totalFiles" -ForegroundColor White
Write-Host "  Total Size: $totalSize MB" -ForegroundColor White
Write-Host ""

if ($allGood) {
    Write-Host "  STATUS: READY FOR TERRAFORM DEPLOYMENT" -ForegroundColor Green
} else {
    Write-Host "  STATUS: SOME FILES MISSING - CHECK WARNINGS" -ForegroundColor Yellow
}

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  NEXT STEPS:" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  1. terraform destroy" -ForegroundColor White
Write-Host "  2. terraform apply" -ForegroundColor White
Write-Host "  3. Wait 15-20 minutes" -ForegroundColor White
Write-Host "  4. Open: http://<master-ip>:30800" -ForegroundColor White
Write-Host "================================================================`n" -ForegroundColor Cyan