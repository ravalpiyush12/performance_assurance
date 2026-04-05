# prepare-deployment.ps1
# Prepares your actual AI platform files for Terraform deployment

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "."
)

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  AI Platform - Preparing Files for Terraform Deployment   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Create app-files directory structure
Write-Host "Creating app-files directory structure..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "app-files" | Out-Null
New-Item -ItemType Directory -Force -Path "app-files/src" | Out-Null
New-Item -ItemType Directory -Force -Path "app-files/src/api" | Out-Null
New-Item -ItemType Directory -Force -Path "app-files/kubernetes" | Out-Null

# Copy main application file (use latest version)
Write-Host "Copying main application code..." -ForegroundColor Yellow
if (Test-Path "$ProjectPath/src/api/main.py") {
    Copy-Item "$ProjectPath/src/api/main.py" "app-files/src/api/" -Force
    Write-Host "  ✓ Copied src/api/main.py" -ForegroundColor Green
} elseif (Test-Path "$ProjectPath/main.py") {
    Copy-Item "$ProjectPath/main.py" "app-files/" -Force
    Write-Host "  ✓ Copied main.py" -ForegroundColor Green
}

# Copy entire src directory
Write-Host "Copying source directory..." -ForegroundColor Yellow
if (Test-Path "$ProjectPath/src") {
    Copy-Item "$ProjectPath/src/*" "app-files/src/" -Recurse -Force
    Write-Host "  ✓ Copied src/" -ForegroundColor Green
}

# Copy Dockerfiles
Write-Host "Copying Dockerfiles..." -ForegroundColor Yellow
if (Test-Path "$ProjectPath/Dockerfile.platform") {
    Copy-Item "$ProjectPath/Dockerfile.platform" "app-files/" -Force
    Write-Host "  ✓ Copied Dockerfile.platform" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Dockerfile.platform not found - will create default" -ForegroundColor Yellow
}

if (Test-Path "$ProjectPath/Dockerfile.sampleapp") {
    Copy-Item "$ProjectPath/Dockerfile.sampleapp" "app-files/" -Force
    Write-Host "  ✓ Copied Dockerfile.sampleapp" -ForegroundColor Green
}

# Copy requirements
Write-Host "Copying requirements..." -ForegroundColor Yellow
if (Test-Path "$ProjectPath/requirements.txt") {
    Copy-Item "$ProjectPath/requirements.txt" "app-files/" -Force
    Write-Host "  ✓ Copied requirements.txt" -ForegroundColor Green
}

# Copy Kubernetes manifests (if they exist)
Write-Host "Checking for Kubernetes manifests..." -ForegroundColor Yellow
if (Test-Path "$ProjectPath/kubernetes") {
    Copy-Item "$ProjectPath/kubernetes/*" "app-files/kubernetes/" -Force
    Write-Host "  ✓ Copied kubernetes/" -ForegroundColor Green
} else {
    Write-Host "  ⚠ kubernetes/ directory not found - will use defaults" -ForegroundColor Yellow
}

# Copy sample app if exists
if (Test-Path "$ProjectPath/sample-app.py") {
    Copy-Item "$ProjectPath/sample-app.py" "app-files/" -Force
    Write-Host "  ✓ Copied sample-app.py" -ForegroundColor Green
}

# Create a manifest of what was copied
Write-Host "`nCreating deployment manifest..." -ForegroundColor Yellow
$manifest = @"
AI Self-Healing Platform - Deployment Files
Generated: $(Get-Date)
Source: $ProjectPath

Files copied to app-files/:
$(Get-ChildItem -Path app-files -Recurse | Select-Object -ExpandProperty FullName | ForEach-Object { "  - " + ($_ -replace [regex]::Escape($PWD.Path + "\app-files"), "") })
"@

$manifest | Out-File "app-files/MANIFEST.txt"

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✓ Files Prepared Successfully!                            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "Files copied to: $(Join-Path $PWD 'app-files')" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Review files in app-files/ directory" -ForegroundColor White
Write-Host "  2. Run: terraform init" -ForegroundColor White
Write-Host "  3. Run: terraform apply`n" -ForegroundColor White

# List what we got
Write-Host "Contents of app-files/:" -ForegroundColor Cyan
Get-ChildItem -Path app-files -Recurse -File | Select-Object FullName | Format-Table -AutoSize
