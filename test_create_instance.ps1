# Test creating an instance
$body = @{
    account_id = "DEMO_BN001"
    platform = "binance"
    strategy = "martingale_hedge"
    symbol = "ETHUSDT"
    parameters = @{
        symbol = "ETHUSDT"
    }
} | ConvertTo-Json -Depth 3

Write-Host "Request body: $body"

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/instances/create" -Method POST -Body $body -ContentType "application/json"
    Write-Host "Success: " -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Error: " -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($_.Exception.Response) {
        $streamReader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        $errorContent = $streamReader.ReadToEnd()
        Write-Host "Response content: $errorContent"
    }
}