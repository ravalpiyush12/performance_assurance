# verify-before-deploy.ps1
# Verify all files are ready before terraform deployment

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Pre-Deployment Verification                               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$allGood = $true

# Check 1: app-files directory exists
Write-Host "1️⃣  Checking app-files directory..." -ForegroundColor Yellow
if (Test-Path "app-files") {
    $fileCount = (Get-ChildItem "app-files" -Recurse -File).Count
    Write-Host "   ✅ app-files/ exists ($fileCount files)" -ForegroundColor Green
} else {
    Write-Host "   ❌ app-files/ not found!" -ForegroundColor Red
    Write-Host "      Run: .\prepare-deployment-complete.ps1 -ProjectPath 'C:\path\to\your\project'" -ForegroundColor Yellow
    $allGood = $false
}

# Check 2: src directory with subdirectories
Write-Host "`n2️⃣  Checking src/ structure..." -ForegroundColor Yellow
if (Test-Path "app-files/src") {
    $srcDirs = Get-ChildItem "app-files/src" -Directory -Recurse
    Write-Host "   ✅ src/ directory exists" -ForegroundColor Green
    Write-Host "      Subdirectories found:" -ForegroundColor Gray
    
    $requiredDirs = @("api", "monitoring", "ml", "orchestrator", "security")
    foreach ($dir in $requiredDirs) {
        if (Test-Path "app-files/src/$dir") {
            Write-Host "      ✓ src/$dir/" -ForegroundColor Green
        } else {
            Write-Host "      ⚠ src/$dir/ - not found" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   ❌ src/ directory not found!" -ForegroundColor Red
    $allGood = $false
}

# Check 3: Main application file
Write-Host "`n3️⃣  Checking main application file..." -ForegroundColor Yellow
$mainFiles = Get-ChildItem "app-files/src/api" -Filter "main*.py" -ErrorAction SilentlyContinue
if ($mainFiles) {
    foreach ($file in $mainFiles) {
        Write-Host "   ✅ Found: src/api/$($file.Name)" -ForegroundColor Green
    }
} else {
    Write-Host "   ❌ No main*.py found in src/api/" -ForegroundColor Red
    $allGood = $false
}

# Check 4: Dockerfiles
Write-Host "`n4️⃣  Checking Dockerfiles..." -ForegroundColor Yellow
$dockerfiles = @("Dockerfile.platform", "Dockerfile.sampleapp")
foreach ($dockerfile in $dockerfiles) {
    if (Test-Path "app-files/$dockerfile") {
        Write-Host "   ✅ $dockerfile exists" -ForegroundColor Green
    } else {
        Write-Host "   ⚠  $dockerfile not found (will use default)" -ForegroundColor Yellow
    }
}

# Check 5: Kubernetes manifests
Write-Host "`n5️⃣  Checking Kubernetes manifests..." -ForegroundColor Yellow
if (Test-Path "app-files/kubernetes") {
    $k8sFiles = Get-ChildItem "app-files/kubernetes" -Filter "*.yaml" -ErrorAction SilentlyContinue
    if ($k8sFiles) {
        foreach ($file in $k8sFiles) {
            Write-Host "   ✅ kubernetes/$($file.Name)" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠  No YAML files in kubernetes/ (will use defaults)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠  kubernetes/ directory not found (will use defaults)" -ForegroundColor Yellow
}

# Check 6: Requirements file
Write-Host "`n6️⃣  Checking requirements.txt..." -ForegroundColor Yellow
if (Test-Path "app-files/requirements.txt") {
    $lineCount = (Get-Content "app-files/requirements.txt").Count
    Write-Host "   ✅ requirements.txt exists ($lineCount packages)" -ForegroundColor Green
} else {
    Write-Host "   ⚠  requirements.txt not found (Docker build may fail)" -ForegroundColor Yellow
}

# Check 7: Terraform configuration
Write-Host "`n7️⃣  Checking Terraform configuration..." -ForegroundColor Yellow
if (Test-Path "terraform.tfvars") {
    Write-Host "   ✅ terraform.tfvars exists" -ForegroundColor Green
    
    # Check SSH key paths
    $tfvarsContent = Get-Content "terraform.tfvars" -Raw
    if ($tfvarsContent -match 'ssh_public_key_path\s*=\s*"([^"]+)"') {
        $publicKeyPath = $matches[1] -replace '~', $env:USERPROFILE
        if (Test-Path $publicKeyPath) {
            Write-Host "   ✅ SSH public key found: $publicKeyPath" -ForegroundColor Green
        } else {
            Write-Host "   ❌ SSH public key NOT found: $publicKeyPath" -ForegroundColor Red
            $allGood = $false
        }
    }
    
    if ($tfvarsContent -match 'ssh_private_key_path\s*=\s*"([^"]+)"') {
        $privateKeyPath = $matches[1] -replace '~', $env:USERPROFILE
        if (Test-Path $privateKeyPath) {
            Write-Host "   ✅ SSH private key found: $privateKeyPath" -ForegroundColor Green
        } else {
            Write-Host "   ❌ SSH private key NOT found: $privateKeyPath" -ForegroundColor Red
            $allGood = $false
        }
    }
} else {
    Write-Host "   ❌ terraform.tfvars not found!" -ForegroundColor Red
    Write-Host "      Run: cp terraform.tfvars.example terraform.tfvars" -ForegroundColor Yellow
    $allGood = $false
}

# Check 8: AWS credentials
Write-Host "`n8️⃣  Checking AWS credentials..." -ForegroundColor Yellow
if ($env:AWS_ACCESS_KEY_ID -and $env:AWS_SECRET_ACCESS_KEY) {
    Write-Host "   ✅ AWS credentials set in environment" -ForegroundColor Green
} else {
    Write-Host "   ⚠  AWS credentials not set in environment" -ForegroundColor Yellow
    Write-Host "      Set them or configure AWS CLI" -ForegroundColor Gray
}

# Check 9: Updated deploy-all.sh
Write-Host "`n9️⃣  Checking deployment script..." -ForegroundColor Yellow
if (Test-Path "scripts/deploy-all.sh") {
    Write-Host "   ✅ scripts/deploy-all.sh exists" -ForegroundColor Green
    
    # Check if it's the updated version
    $scriptContent = Get-Content "scripts/deploy-all.sh" -Raw
    if ($scriptContent -match "USING YOUR ACTUAL CODE" -or $scriptContent -match "kubernetes-fixed") {
        Write-Host "   ✅ Using updated deployment script" -ForegroundColor Green
    } else {
        Write-Host "   ⚠  May be using old deployment script" -ForegroundColor Yellow
        Write-Host "      Consider updating with deploy-all-final.sh" -ForegroundColor Gray
    }
} else {
    Write-Host "   ❌ scripts/deploy-all.sh not found!" -ForegroundColor Red
    $allGood = $false
}

# Check 10: Terraform initialized
Write-Host "`n🔟 Checking Terraform initialization..." -ForegroundColor Yellow
if (Test-Path ".terraform") {
    Write-Host "   ✅ Terraform initialized (.terraform/ exists)" -ForegroundColor Green
} else {
    Write-Host "   ⚠  Terraform not initialized" -ForegroundColor Yellow
    Write-Host "      Run: terraform init" -ForegroundColor Gray
}

# Final summary
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "║  ✅ ALL CHECKS PASSED - READY TO DEPLOY!                  ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    Write-Host "🚀 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. terraform init    (if not already done)" -ForegroundColor White
    Write-Host "   2. terraform plan    (review changes)" -ForegroundColor White
    Write-Host "   3. terraform apply   (deploy!)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "║  ⚠️  SOME CHECKS FAILED - FIX ISSUES FIRST               ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    Write-Host "❌ Fix the issues above before deploying" -ForegroundColor Red
    Write-Host ""
}

# Display file count summary
if (Test-Path "app-files") {
    Write-Host "📊 File Summary:" -ForegroundColor Cyan
    Write-Host "   Total files ready for upload: $(( Get-ChildItem "app-files" -Recurse -File).Count)" -ForegroundColor White
    Write-Host "   Total size: $([math]::Round((( Get-ChildItem "app-files" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB), 2)) MB" -ForegroundColor White
    Write-Host ""
}
