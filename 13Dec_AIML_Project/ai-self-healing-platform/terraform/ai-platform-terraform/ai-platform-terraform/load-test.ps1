# AI Self-Healing Platform - Load Testing Script
# Run this after Terraform deployment to trigger self-healing

param(
    [Parameter(Mandatory=$true)]
    [string]$MasterIP,
    
    [string]$TestType = "both"  # Options: cpu, error, both
)

$DashboardURL = "http://${MasterIP}:30800"
$AppURL = "http://${MasterIP}:30080"

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   AI SELF-HEALING PLATFORM - LOAD TEST                     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "Dashboard: $DashboardURL" -ForegroundColor Green
Write-Host "App URL:   $AppURL`n" -ForegroundColor Green

if ($TestType -eq "cpu" -or $TestType -eq "both") {
    Write-Host "═══ CPU LOAD TEST ═══" -ForegroundColor Yellow
    Write-Host "Generating high CPU load to trigger scaling...`n" -ForegroundColor White
    
    for ($batch = 1; $batch -le 15; $batch++) {
        $concurrent = [Math]::Min($batch * 4, 40)
        
        Write-Host "Batch $batch/15 - Sending $concurrent concurrent requests..." -ForegroundColor Cyan
        
        $jobs = 1..$concurrent | ForEach-Object {
            Start-Job -ScriptBlock {
                param($url)
                try {
                    Invoke-WebRequest -Uri "$url/compute" -UseBasicParsing -TimeoutSec 5 | Out-Null
                } catch {}
            } -ArgumentList $AppURL
        }
        
        $jobs | Wait-Job -Timeout 5 | Remove-Job -Force
        Get-Job | Remove-Job -Force
        
        Start-Sleep -Seconds 2
    }
    
    Write-Host "`n✓ CPU load test complete!" -ForegroundColor Green
    Write-Host "Check dashboard for CPU_USAGE anomaly and pod scaling`n" -ForegroundColor White
}

if ($TestType -eq "error" -or $TestType -eq "both") {
    Write-Host "═══ ERROR RATE TEST ═══" -ForegroundColor Yellow
    Write-Host "Generating errors to populate error rate graph...`n" -ForegroundColor White
    
    for ($i = 1; $i -le 30; $i++) {
        try {
            Invoke-WebRequest -Uri "$AppURL/error" -ErrorAction Stop | Out-Null
        } catch {
            # Expected - endpoint returns 500
        }
        
        if ($i % 10 -eq 0) {
            Write-Host "Generated $i errors" -ForegroundColor Red
        }
        
        Start-Sleep -Milliseconds 200
    }
    
    Write-Host "`n✓ Error generation complete!" -ForegroundColor Green
    Write-Host "Refresh dashboard to see error rate graph`n" -ForegroundColor White
}

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   LOAD TEST COMPLETE - CHECK RESULTS                       ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "Dashboard:  $DashboardURL" -ForegroundColor Yellow
Write-Host "Prometheus: http://${MasterIP}:30090" -ForegroundColor Yellow

Write-Host "`nExpected results:" -ForegroundColor White
Write-Host "  • CPU spike in graphs" -ForegroundColor Gray
Write-Host "  • CPU_USAGE anomaly detected" -ForegroundColor Gray
Write-Host "  • HPA triggers pod scaling (4 → 6+ pods)" -ForegroundColor Gray
Write-Host "  • Self-healing actions logged" -ForegroundColor Gray
Write-Host "  • Error rate graph populated`n" -ForegroundColor Gray
