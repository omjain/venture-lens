# PowerShell test script for /score endpoint
$API_URL = "http://localhost:8000"

# Test data
$testData = @{
    idea = @"
AI-powered platform for healthcare data analysis that helps hospitals reduce costs 
by 30% through predictive analytics. Uses machine learning to identify patterns in 
patient data and optimize resource allocation. Unique approach combines real-time 
monitoring with historical data analysis.
"@
    team = @"
Founding team includes 2 ex-Google engineers with 10+ years ML experience, 
1 healthcare veteran who previously built a successful healthtech startup, 
and 1 data scientist with PhD in biostatistics. Combined experience of 35+ years 
in healthcare and technology. Strong technical and domain expertise.
"@
    traction = @"
Currently have 50 paying customers (hospitals), generating $50K MRR. 
Growing at 20% month-over-month. Signed 3 enterprise contracts in last quarter. 
Product is proven to reduce costs by average of 28%. Customer retention rate of 95%.
"@
    market = @"
Healthcare analytics market is $50B+ globally and growing at 15% CAGR. 
Large addressable market with 6,000+ hospitals in US alone. Market is fragmented 
with no clear dominant player. Growing demand for cost reduction in healthcare 
driven by regulatory pressures.
"@
    startup_name = "HealthTech AI"
} | ConvertTo-Json -Depth 10

Write-Host "🧪 Testing /score endpoint..." -ForegroundColor Cyan
Write-Host "📤 Sending request to $API_URL/score`n" -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "$API_URL/score" `
        -Method POST `
        -ContentType "application/json" `
        -Body $testData `
        -UseBasicParsing
    
    $result = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Success! Response received:`n" -ForegroundColor Green
    $result | ConvertTo-Json -Depth 10 | Write-Host
    
    Write-Host "`n📊 Summary:" -ForegroundColor Yellow
    Write-Host "   Overall Score: $($result.overall_score)/10"
    Write-Host "   Confidence: $($result.confidence)"
    Write-Host "   Recommendation: $($result.recommendation)"
    Write-Host "`n   Breakdown:"
    Write-Host "   - Idea: $($result.breakdown.idea_score)/10"
    Write-Host "   - Team: $($result.breakdown.team_score)/10"
    Write-Host "   - Traction: $($result.breakdown.traction_score)/10"
    Write-Host "   - Market: $($result.breakdown.market_score)/10"
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response: $responseBody" -ForegroundColor Red
    }
}

