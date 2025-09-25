# deployment/deploy_ai_service.ps1
# Enhanced AI Agent Service deployment script with buildpack support

param(
    [string]$ProjectId = "ai-chatbot-472322",
    [string]$Region = "us-central1",
    [string]$ServiceName = "ai-agent-service"
)

Write-Host "🚀 Deploying Enhanced AI Agent Service with buildpack..." -ForegroundColor Green
Write-Host "📁 Current directory: $(Get-Location)" -ForegroundColor Cyan

# Verify gcloud authentication
Write-Host "🔍 Verifying gcloud authentication..." -ForegroundColor Yellow
try {
    $authStatus = gcloud auth list --filter="status:ACTIVE" --format="value(account)" 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($authStatus)) {
        Write-Host "❌ No active gcloud authentication found" -ForegroundColor Red
        Write-Host "💡 Run: gcloud auth login" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Authenticated as: $authStatus" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to check gcloud authentication: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Verify buildpack configuration files
Write-Host "🔍 Checking buildpack configuration files..." -ForegroundColor Yellow
$buildpackFiles = @(
    @{Name=".python-version"; Expected="3.11"; Description="Python version"},
    @{Name="runtime.txt"; Expected="python-3.11"; Description="Runtime specification"},
    @{Name="Procfile"; Expected="web: python main.py"; Description="Process specification"}
)

foreach ($file in $buildpackFiles) {
    if (-not (Test-Path $file.Name)) {
        Write-Host "❌ Buildpack file missing: $($file.Name)" -ForegroundColor Red
        Write-Host "   Expected content: $($file.Expected)" -ForegroundColor Gray
        exit 1
    } else {
        $content = (Get-Content $file.Name -Raw).Trim()
        if ($content -eq $file.Expected) {
            Write-Host "✅ Found: $($file.Name) ($($file.Description))" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $($file.Name) content mismatch:" -ForegroundColor Yellow
            Write-Host "   Found: '$content'" -ForegroundColor Gray
            Write-Host "   Expected: '$($file.Expected)'" -ForegroundColor Gray
        }
    }
}

# Verify vector files exist
Write-Host "🔍 Checking vector files..." -ForegroundColor Yellow
$vectorPath = "app/vector-files"
if (-not (Test-Path $vectorPath)) {
    Write-Host "❌ Vector files directory not found: $vectorPath" -ForegroundColor Red
    exit 1
}

$vectorFiles = Get-ChildItem $vectorPath -File
Write-Host "✅ Found $($vectorFiles.Count) vector files in $vectorPath" -ForegroundColor Green

# Create temporary environment file
$tempEnvFile = "temp-env-vars.txt"
Write-Host "📝 Creating environment variables file..." -ForegroundColor Yellow

# Build environment variables
$envVars = @{
    "PROJECT_ID" = $ProjectId
    "LOCATION" = $Region
    "IS_LOCAL" = "false"
    "LOCAL_VECTOR_FILES_PATH" = "app/vector-files"
    "FAISS_INDEX_TYPE" = "IVF"
    "CORS_ORIGINS" = "https://ai-chatbot-472322.web.app,http://localhost:3000"
    "DEBUG_MODE" = "true"
    "LOG_QUERIES" = "false"
    "EMBEDDING_QUANT" = "10"
    "FIREBASE_STORAGE_BUCKET" = "ai-chatbot-472322.appspot.com"
}

try {
    # Write environment variables to file
    $envContent = @()
    foreach ($key in $envVars.Keys) {
        $value = $envVars[$key]
        $envContent += "$key=$value"
    }

    $envContent | Set-Content -Path $tempEnvFile -Encoding UTF8
    Write-Host "   Created: $tempEnvFile with $($envContent.Count) variables" -ForegroundColor Gray

    # Deploy with buildpack
    Write-Host "🚀 Starting Cloud Run deployment..." -ForegroundColor Green

    $deployArgs = @(
        "run", "deploy", $ServiceName,
        "--source", ".",
        "--region", $Region,
        "--allow-unauthenticated",
        "--service-account", "ai-agent-runner@$ProjectId.iam.gserviceaccount.com",
        "--env-vars-file", $tempEnvFile,
        "--memory", "4Gi",
        "--cpu", "2",
        "--max-instances", "10",
        "--timeout", "300",
        "--platform", "managed",
        "--project", $ProjectId
    )

    Write-Host "   Command: gcloud $($deployArgs -join ' ')" -ForegroundColor Gray
    & gcloud $deployArgs

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Cloud Run deployment failed" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ AI Agent Service deployed successfully!" -ForegroundColor Green

    # Get service URL
    Write-Host "🔍 Getting service URL..." -ForegroundColor Yellow
    $ServiceUrl = gcloud run services describe $ServiceName --region $Region --format "value(status.url)" --project $ProjectId 2>$null

    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrEmpty($ServiceUrl)) {
        Write-Host "🔗 Service URL: $ServiceUrl" -ForegroundColor Cyan

        # Test health endpoint
        Write-Host "🧪 Testing health endpoint..." -ForegroundColor Yellow
        Start-Sleep -Seconds 15

        try {
            $healthResponse = Invoke-RestMethod -Uri "$ServiceUrl/health" -Method Get -TimeoutSec 30
            Write-Host "✅ Health check passed" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Health check failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️ Could not retrieve service URL" -ForegroundColor Yellow
    }

} finally {
    # Clean up temp file
    if (Test-Path $tempEnvFile) {
        Remove-Item $tempEnvFile -Force
        Write-Host "🧹 Cleaned up temporary environment file" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "✅ Buildpack deployment complete!" -ForegroundColor Green
Write-Host "🔗 Service URL: $ServiceUrl" -ForegroundColor Cyan
Write-Host "📦 Deployment method: Cloud Buildpacks" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test: python deployment/test_ai_service.py" -ForegroundColor White
Write-Host "2. Monitor: gcloud logging read resource.type=cloud_run_revision" -ForegroundColor White