# prepare-deployment-fixed.ps1
# Prepares your COMPLETE AI platform project for Terraform deployment
# Fixed to handle kubernetes/ folder

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
    Copy-Item "$ProjectPath/src" "app-files/" -Recurse -Force
    
    $fileCount = (Get-ChildItem "app-files/src" -Recurse -File).Count
    $dirCount = (Get-ChildItem "app-files/src" -Recurse -Directory).Count
    
    Write-Host "  SUCCESS: Copied src/ directory" -ForegroundColor Green
    Write-Host "     - $dirCount subdirectories" -ForegroundColor Gray
    Write-Host "     - $fileCount files" -ForegroundColor Gray
    
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
# COPY KUBERNETES FOLDER (ENTIRE DIRECTORY)
# ============================================================================

Write-Host "`nCopying Kubernetes manifests..." -ForegroundColor Yellow

# Check if kubernetes folder exists
if (Test-Path "$ProjectPath/kubernetes") {
    # Copy entire kubernetes folder
    Copy-Item "$ProjectPath/kubernetes/*" "app-files/kubernetes/" -Recurse -Force -ErrorAction SilentlyContinue
    
    $k8sFileCount = (Get-ChildItem "app-files/kubernetes" -File -ErrorAction SilentlyContinue).Count
    if ($k8sFileCount -gt 0) {
        Write-Host "  SUCCESS: Copied kubernetes/ folder ($k8sFileCount files)" -ForegroundColor Green
        Get-ChildItem "app-files/kubernetes" -File | ForEach-Object {
            Write-Host "     OK: kubernetes/$($_.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  WARNING: kubernetes/ folder empty" -ForegroundColor Yellow
    }
} else {
    # Try to find individual YAML files in root
    Write-Host "  kubernetes/ folder not found, looking for YAML files in root..." -ForegroundColor Yellow
    
    $k8sFiles = @("ai-platform.yaml", "sample-app.yaml", "kubernetes-sample.yaml")
    $copiedCount = 0
    
    foreach ($file in $k8sFiles) {
        if (Test-Path "$ProjectPath/$file") {
            Copy-Item "$ProjectPath/$file" "app-files/kubernetes/" -Force
            Write-Host "  SUCCESS: Copied $file" -ForegroundColor Green
            $copiedCount++
        }
    }
    
    if ($copiedCount -eq 0) {
        Write-Host "  WARNING: No Kubernetes manifests found (will use defaults)" -ForegroundColor Yellow
    }
}

# ============================================================================
# COPY SAMPLE APP (different naming variations)
# ============================================================================

Write-Host "`nCopying sample app..." -ForegroundColor Yellow

$sampleAppFiles = @("sample-app.py", "sample_app.py", "sampleapp.py")
$sampleAppCopied = $false

foreach ($file in $sampleAppFiles) {
    if (Test-Path "$ProjectPath/$file") {
        Copy-Item "$ProjectPath/$file" "app-files/sample-app.py" -Force
        Write-Host "  SUCCESS: Copied $file as sample-app.py" -ForegroundColor Green
        $sampleAppCopied = $true
        break
    }
}

if (-not $sampleAppCopied) {
    Write-Host "  WARNING: sample-app.py not found (will use default)" -ForegroundColor Yellow
}

# ============================================================================
# COPY ADDITIONAL FILES
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

$allFiles = Get-ChildItem -Path "app-files" -Recurse -File
$totalSize = [math]::Round(($allFiles | Measure-Object -Property Length -Sum).Sum / 1MB, 2)

$manifest = @"
================================================================
AI SELF-HEALING PLATFORM - DEPLOYMENT MANIFEST
================================================================

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Source: $ProjectPath
Target: app-files/

================================================================
DEPLOYMENT SUMMARY
================================================================

Total Files: $($allFiles.Count)
Total Size: $totalSize MB

Directory Structure:
----------------------------------------------------------------
"@

Get-ChildItem -Path "app-files" -Recurse -Directory | Sort-Object FullName | ForEach-Object {
    $relativePath = $_.FullName -replace [regex]::Escape($PWD.Path + "\app-files"), ""
    $fileCount = (Get-ChildItem $_.FullName -File).Count
    $manifest += "`n  Folder: .$relativePath ($fileCount files)"
}

$manifest += "`n`nKey Files:`n"
$manifest += "----------------------------------------------------------------`n"

$importantPatterns = @(
    "Dockerfile*",
    "requirements.txt",
    "*.yaml",
    "sample-app.py",
    "src/api/main*.py"
)

foreach ($pattern in $importantPatterns) {
    Get-ChildItem -Path "app-files" -Recurse -File -Include $pattern | ForEach-Object {
        $relativePath = $_.FullName -replace [regex]::Escape($PWD.Path + "\app-files"), ""
        $size = [math]::Round($_.Length / 1KB, 1)
        $manifest += "`n  OK: .$relativePath ($size KB)"
    }
}

$manifest += "`n`n================================================================`n"
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
Write-Host "  Total Size: $totalSize MB" -ForegroundColor White
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
Write-Host "  1. Review files: Get-ChildItem app-files -Recurse" -ForegroundColor White
Write-Host "  2. Check manifest: Get-Content app-files\DEPLOYMENT_MANIFEST.txt" -ForegroundColor White
Write-Host "  3. Run: terraform init" -ForegroundColor White
Write-Host "  4. Run: terraform apply" -ForegroundColor White
Write-Host ""

# Verify critical files
Write-Host "Verification:" -ForegroundColor Yellow

$criticalChecks = @{
    "src/api/main.py" = "app-files/src/api/main.py"
    "Dockerfile.platform" = "app-files/Dockerfile.platform"
    "requirements.txt" = "app-files/requirements.txt"
}

$allCriticalPresent = $true
foreach ($check in $criticalChecks.GetEnumerator()) {
    if (Test-Path $check.Value) {
        Write-Host "  SUCCESS: $($check.Key)" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $($check.Key)" -ForegroundColor Red
        $allCriticalPresent = $false
    }
}

# Check Kubernetes files
$k8sExists = (Get-ChildItem "app-files/kubernetes" -File -ErrorAction SilentlyContinue).Count -gt 0
if ($k8sExists) {
    Write-Host "  SUCCESS: Kubernetes manifests ($(( Get-ChildItem 'app-files/kubernetes' -File).Count) files)" -ForegroundColor Green
} else {
    Write-Host "  INFO: No Kubernetes manifests (will use defaults)" -ForegroundColor Yellow
}

Write-Host ""

if ($allCriticalPresent) {
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "  READY FOR DEPLOYMENT!" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
} else {
    Write-Host "================================================================" -ForegroundColor Yellow
    Write-Host "  Some files missing - deployment will use defaults" -ForegroundColor Yellow
    Write-Host "================================================================" -ForegroundColor Yellow
}

Write-Host ""
