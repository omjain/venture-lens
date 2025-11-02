# Testing the /ingest Endpoint

## PowerShell Commands

PowerShell's `curl` is an alias for `Invoke-WebRequest` and uses different syntax.

### Test PDF Upload (PowerShell)

```powershell
# Method 1: Using Invoke-WebRequest
$filePath = "pitchdeck.pdf"
$uri = "http://localhost:8000/ingest"
$form = @{
    file = Get-Item -Path $filePath
}
Invoke-WebRequest -Uri $uri -Method Post -Form $form

# Method 2: Using Invoke-RestMethod (returns JSON directly)
$filePath = "pitchdeck.pdf"
$uri = "http://localhost:8000/ingest"
$form = @{
    file = Get-Item -Path $filePath
}
$response = Invoke-RestMethod -Uri $uri -Method Post -Form $form
$response | ConvertTo-Json -Depth 10
```

### Test URL Scraping (PowerShell)

```powershell
# Using Invoke-RestMethod
$uri = "http://localhost:8000/ingest"
$body = @{
    url = "https://example.com/startup"
}
$response = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
$response | ConvertTo-Json -Depth 10
```

## Alternative: Use curl.exe (Windows)

If you have curl.exe installed separately, use the full path:

```powershell
# Use curl.exe instead of curl alias
& "C:\Windows\System32\curl.exe" -X POST "http://localhost:8000/ingest" -F "file=@pitchdeck.pdf"
```

## Python Test Script

Create a simple test script:

```python
import requests

# Test PDF upload
with open('pitchdeck.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/ingest', files=files)
    print(response.json())

# Test URL
data = {'url': 'https://example.com/startup'}
response = requests.post('http://localhost:8000/ingest', data=data)
print(response.json())
```

## Browser Testing (Postman/Swagger UI)

1. FastAPI automatically generates Swagger UI:
   - Visit: http://localhost:8000/docs
   - Find the `/ingest` endpoint
   - Test directly from the browser interface

