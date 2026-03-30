# Test script for deployed Budget MCP Server
# Usage: .\test-mcp-endpoint.ps1 -Endpoint "https://your-app.azurecontainerapps.io"

param(
    [Parameter(Mandatory=$true)]
    [string]$Endpoint
)

# Remove trailing slash if present
$Endpoint = $Endpoint.TrimEnd('/')

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Testing Budget MCP Server" -ForegroundColor Cyan
Write-Host "Endpoint: $Endpoint" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health check
Write-Host "[Test 1/4] Health check (GET /)..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$Endpoint/" -Method Get -ErrorAction Stop
    Write-Host "✅ Health check passed" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 2: List available tools
Write-Host "[Test 2/4] Listing available MCP tools..." -ForegroundColor Yellow
try {
    $tools = Invoke-RestMethod -Uri "$Endpoint/mcp/list_tools" -Method Get -ErrorAction Stop
    Write-Host "✅ Found $($tools.tools.Count) tools:" -ForegroundColor Green
    foreach ($tool in $tools.tools) {
        Write-Host "   - $($tool.name)" -ForegroundColor White
    }
    Write-Host ""
} catch {
    Write-Host "❌ Failed to list tools: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 3: Call budget_list_departments
Write-Host "[Test 3/4] Calling budget_list_departments..." -ForegroundColor Yellow
try {
    $body = @{
        name = "budget_list_departments"
        arguments = @{}
    } | ConvertTo-Json

    $result = Invoke-RestMethod -Uri "$Endpoint/mcp/call_tool" -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
    
    if ($result.content -and $result.content[0].text) {
        $data = $result.content[0].text | ConvertFrom-Json
        Write-Host "✅ Successfully retrieved department data" -ForegroundColor Green
        Write-Host "   Departments:" -ForegroundColor White
        foreach ($dept in $data.departments) {
            Write-Host "   - [$($dept.department_code)] $($dept.department_name)" -ForegroundColor Gray
        }
        Write-Host ""
    } else {
        Write-Host "⚠️ Unexpected response format" -ForegroundColor Yellow
        Write-Host ""
    }
} catch {
    Write-Host "❌ Failed to call tool: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 4: Call budget_get_variance_policy
Write-Host "[Test 4/4] Calling budget_get_variance_policy..." -ForegroundColor Yellow
try {
    $body = @{
        name = "budget_get_variance_policy"
        arguments = @{}
    } | ConvertTo-Json

    $result = Invoke-RestMethod -Uri "$Endpoint/mcp/call_tool" -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
    
    if ($result.content -and $result.content[0].text) {
        $policy = $result.content[0].text | ConvertFrom-Json
        Write-Host "✅ Successfully retrieved variance policy" -ForegroundColor Green
        Write-Host "   Policy Name: $($policy.policy_name)" -ForegroundColor White
        Write-Host "   Version: $($policy.version)" -ForegroundColor White
        Write-Host "   Variance Bands: $($policy.variance_bands.Count)" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "⚠️ Unexpected response format" -ForegroundColor Yellow
        Write-Host ""
    }
} catch {
    Write-Host "❌ Failed to call tool: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

Write-Host "================================================" -ForegroundColor Green
Write-Host "Testing Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test with MCP Inspector:" -ForegroundColor Yellow
Write-Host "   npx @modelcontextprotocol/inspector $Endpoint/mcp" -ForegroundColor White
Write-Host ""
Write-Host "2. Use in your workflow:" -ForegroundColor Yellow
Write-Host "   Update MCP_SERVER_URL in budget_variance_workflow.py to:" -ForegroundColor White
Write-Host "   MCP_SERVER_URL = `"$Endpoint/mcp`"" -ForegroundColor White
Write-Host ""

