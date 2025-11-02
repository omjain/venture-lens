# PowerShell script to test the /ingest endpoint
# Usage: .\test_ingest_endpoint.ps1

Write-Host "=== Testing Venture Lens Data Ingestion Agent ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Check if server is running
Write-Host "1. Checking if FastAPI server is running..." -ForegroundColor Yellow
try {
    $healthCheck = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -ErrorAction Stop
    Write-Host "   [OK] Server is running!" -ForegroundColor Green
    Write-Host "   Status: $($healthCheck.status)" -ForegroundColor Gray
} catch {
    Write-Host "   [ERROR] Server not running on $baseUrl" -ForegroundColor Red
    Write-Host "   Start server with: cd api && python -m uvicorn main:app --reload --port 8000" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 1: URL Ingestion
Write-Host "2. Testing URL ingestion..." -ForegroundColor Yellow
try {
    $body = @{
        url = "https://example.com"
    }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/ingest" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded" -ErrorAction Stop
    
    Write-Host "   [OK] URL ingestion successful!" -ForegroundColor Green
    Write-Host "   Startup Name: $($response.startup_name)" -ForegroundColor Gray
    Write-Host "   Source Type: $($response._metadata.source_type)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Full Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 5 | Write-Host
    
} catch {
    Write-Host "   [WARNING] URL ingestion test failed: $($_.Exception.Message)" -ForegroundColor Yellow
    if ($_.ErrorDetails.Message) {
        Write-Host "   Details: $($_.ErrorDetails.Message)" -ForegroundColor Gray
    }
}

Write-Host ""

# Test 2: PDF Upload (if file exists)
Write-Host "3. Testing PDF upload..." -ForegroundColor Yellow
$pdfFiles = @("pitchdeck.pdf", "test.pdf", "sample.pdf")

$pdfFound = $false
foreach ($pdfFile in $pdfFiles) {
    if (Test-Path $pdfFile) {
        $pdfFound = $true
        Write-Host "   Found PDF: $pdfFile" -ForegroundColor Gray
        
        try {
            $form = @{
                file = Get-Item -Path $pdfFile
            }
            
            $response = Invoke-RestMethod -Uri "$baseUrl/ingest" -Method Post -Form $form -ErrorAction Stop
            
            Write-Host "   [OK] PDF ingestion successful!" -ForegroundColor Green
            Write-Host "   Startup Name: $($response.startup_name)" -ForegroundColor Gray
            Write-Host "   Total Slides: $($response._metadata.total_slides)" -ForegroundColor Gray
            Write-Host ""
            Write-Host "   Full Response:" -ForegroundColor Cyan
            $response | ConvertTo-Json -Depth 5 | Write-Host
            
        } catch {
            Write-Host "   [WARNING] PDF ingestion test failed: $($_.Exception.Message)" -ForegroundColor Yellow
            if ($_.ErrorDetails.Message) {
                Write-Host "   Details: $($_.ErrorDetails.Message)" -ForegroundColor Gray
            }
        }
        break
    }
}

if (-not $pdfFound) {
    Write-Host "   [INFO] No PDF file found to test. Create a pitchdeck.pdf file to test PDF upload." -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
