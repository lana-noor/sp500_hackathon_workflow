# Pre-flight check for Budget Variance Workflow
# Verifies all requirements before running the workflow

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Budget Variance Workflow - Pre-flight Check" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check 1: Python virtual environment
Write-Host "[1/6] Checking Python virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\activate.ps1") {
    Write-Host "   ✅ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "   ❌ Virtual environment not found at venv\Scripts\activate.ps1" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 2: .env file
Write-Host "[2/6] Checking .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   ✅ .env file found" -ForegroundColor Green
    
    # Check for required variables
    $envContent = Get-Content ".env" -Raw
    
    if ($envContent -match "AZURE_AI_PROJECT_ENDPOINT") {
        Write-Host "   ✅ AZURE_AI_PROJECT_ENDPOINT is set" -ForegroundColor Green
    } else {
        Write-Host "   ❌ AZURE_AI_PROJECT_ENDPOINT is missing" -ForegroundColor Red
        $allGood = $false
    }
    
    if ($envContent -match "AZURE_AI_MODEL_DEPLOYMENT_NAME") {
        Write-Host "   ✅ AZURE_AI_MODEL_DEPLOYMENT_NAME is set" -ForegroundColor Green
    } else {
        Write-Host "   ❌ AZURE_AI_MODEL_DEPLOYMENT_NAME is missing" -ForegroundColor Red
        $allGood = $false
    }
    
    if ($envContent -match "MCP_SERVER_URL=https://budget-mcp-server") {
        Write-Host "   ✅ MCP_SERVER_URL is set to remote endpoint" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  MCP_SERVER_URL may not be set correctly" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ .env file not found" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 3: Azure CLI login
Write-Host "[3/6] Checking Azure CLI login..." -ForegroundColor Yellow
try {
    $account = az account show 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Logged into Azure CLI" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Not logged into Azure CLI - run: az login" -ForegroundColor Red
        $allGood = $false
    }
} catch {
    Write-Host "   ❌ Azure CLI not installed or not in PATH" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 4: MCP Server accessibility
Write-Host "[4/6] Checking MCP Server endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "https://budget-mcp-server.redwave-ed431b4a.eastus.azurecontainerapps.io/mcp/list_tools" -Method Get -ErrorAction Stop -TimeoutSec 5
    if ($response.tools) {
        Write-Host "   ✅ MCP Server is accessible ($($response.tools.Count) tools available)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  MCP Server responded but no tools found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Cannot reach MCP Server: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "      Make sure the server is deployed and running" -ForegroundColor Gray
    $allGood = $false
}
Write-Host ""

# Check 5: Required Python packages
Write-Host "[5/6] Checking Python packages..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\python.exe") {
    $packages = & "venv\Scripts\python.exe" -m pip list 2>&1
    
    $requiredPackages = @("azure-ai-projects", "azure-identity", "agent-framework", "fastmcp", "python-dotenv", "pydantic")
    $missingPackages = @()
    
    foreach ($pkg in $requiredPackages) {
        if ($packages -match $pkg) {
            Write-Host "   ✅ $pkg installed" -ForegroundColor Green
        } else {
            Write-Host "   ❌ $pkg not installed" -ForegroundColor Red
            $missingPackages += $pkg
            $allGood = $false
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Host ""
        Write-Host "   To install missing packages, run:" -ForegroundColor Yellow
        Write-Host "   pip install $($missingPackages -join ' ')" -ForegroundColor White
    }
} else {
    Write-Host "   ⚠️  Cannot check packages - venv Python not found" -ForegroundColor Yellow
}
Write-Host ""

# Check 6: Output directory
Write-Host "[6/6] Checking output directory..." -ForegroundColor Yellow
$outputDir = "C:\Users\lananoor\OneDrive - Microsoft\FAB\DigitalTransformationDEMO"
if (Test-Path $outputDir) {
    Write-Host "   ✅ Output directory exists: $outputDir" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Output directory does not exist (will be created): $outputDir" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "✅ All checks passed! Ready to run workflow" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To run the workflow:" -ForegroundColor Yellow
    Write-Host "  1. Activate venv: .\venv\Scripts\activate" -ForegroundColor White
    Write-Host "  2. Run workflow: python budget_variance_workflow.py" -ForegroundColor White
} else {
    Write-Host "❌ Some checks failed - please fix the issues above" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Cyan
}
Write-Host ""

