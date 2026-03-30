# Simple deployment script for Budget MCP Server to Azure Container Apps
# This version prompts for configuration and provides step-by-step feedback

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Budget MCP Server - Azure Container Apps Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is installed
try {
    $null = az --version
} catch {
    Write-Error "Azure CLI is not installed. Please install from: https://aka.ms/azure-cli"
    exit 1
}

# Check if logged in
Write-Host "Checking Azure login status..." -ForegroundColor Yellow
$account = az account show 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in to Azure. Logging in..." -ForegroundColor Yellow
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to login to Azure"
        exit 1
    }
}

# Get configuration from user or use defaults
Write-Host ""
Write-Host "Configuration (press Enter to use defaults):" -ForegroundColor Cyan
$RESOURCE_GROUP = Read-Host "Resource Group name [rg-mcp-server]"
if ([string]::IsNullOrWhiteSpace($RESOURCE_GROUP)) { $RESOURCE_GROUP = "rg-mcp-server" }

$LOCATION = Read-Host "Azure region [eastus]"
if ([string]::IsNullOrWhiteSpace($LOCATION)) { $LOCATION = "eastus" }

$RANDOM_SUFFIX = Get-Random -Minimum 1000 -Maximum 9999
$ACR_NAME = Read-Host "Container Registry name [acrmcp$RANDOM_SUFFIX]"
if ([string]::IsNullOrWhiteSpace($ACR_NAME)) { $ACR_NAME = "acrmcp$RANDOM_SUFFIX" }

$CONTAINER_APP_NAME = Read-Host "Container App name [budget-mcp-server]"
if ([string]::IsNullOrWhiteSpace($CONTAINER_APP_NAME)) { $CONTAINER_APP_NAME = "budget-mcp-server" }

Write-Host ""
Write-Host "Deployment Configuration:" -ForegroundColor Green
Write-Host "  Resource Group: $RESOURCE_GROUP" -ForegroundColor White
Write-Host "  Location: $LOCATION" -ForegroundColor White
Write-Host "  Container Registry: $ACR_NAME" -ForegroundColor White
Write-Host "  Container App: $CONTAINER_APP_NAME" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Proceed with deployment? [Y/n]"
if ($confirm -eq 'n' -or $confirm -eq 'N') {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Starting deployment..." -ForegroundColor Green
Write-Host ""

# Execute deployment
$env:RESOURCE_GROUP = $RESOURCE_GROUP
$env:LOCATION = $LOCATION
$env:ACR_NAME = $ACR_NAME
$env:CONTAINER_APP_NAME = $CONTAINER_APP_NAME
$env:CONTAINER_APP_ENV = "$CONTAINER_APP_NAME-env"
$env:IMAGE_NAME = "budget-reports-mcp-server"
$env:IMAGE_TAG = "latest"

# Run the main deployment script
.\deploy-to-aca.ps1

