# deployment/deploy_ai_service.ps1

param(
    [string]$ProjectId = "ai-chatbot-472322",
    [string]$Region = "us-central1",
    [string]$ServiceName = "ai-agent-service"
)

Write-Host "🚀 Deploying Enhanced AI Agent Service with buildpack..." -ForegroundColor Green

# Verify we're in the right directory
$currentPath = Get-Location
Write-Host "📁 Current directory: $currentPath" -ForegroundColor Cyan

# Verify vector files exist locally (check both enhanced and legacy)
Write-Host "🔍 Checking local vector files..." -ForegroundColor Yellow
$vectorFilesPath = "app/vector-files"

$enhancedFiles = @(
    "embeddings_enhanced.npy",
    "metadata_enhanced.pkl", 
    "index_to_id_enhanced.pkl",
    "faiss_index_enhanced.index"
)

$legacyFiles = @(
    "manual001_embeddings.npy",
    "manual001_metadata.pkl", 
    "manual001_index_to_id.pkl"
)

if (-not (Test-Path $vectorFilesPath)) {
    Write-Host "❌ Vector files directory not found: $vectorFilesPath" -ForegroundColor Red
    exit 1
}

# Check for enhanced files first
$hasEnhancedFiles = $true
$enhancedFilesFound = @()

foreach ($file in $enhancedFiles) {
    $filePath = Join-Path $vectorFilesPath $file
    if (Test-Path $filePath) {
        $fileSize = (Get-Item $filePath).Length
        Write-Host "✅ Found enhanced: $file ($([math]::Round($fileSize/1MB, 2)) MB)" -ForegroundColor Green
        $enhancedFilesFound += $file
    } else {
        Write-Host "⚠️ Enhanced file missing: $file" -ForegroundColor Yellow
        $hasEnhancedFiles = $false
    }
}

# Check for legacy files if enhanced not complete
if (-not $hasEnhancedFiles) {
    Write-Host "🔄 Checking for legacy files..." -ForegroundColor Yellow
    $hasLegacyFiles = $true
    
    foreach ($file in $legacyFiles) {
        $filePath = Join-Path $vectorFilesPath $file
        if (Test-Path $filePath) {
            $fileSize = (Get-Item $filePath).Length
            Write-Host "✅ Found legacy: $file ($([math]::Round($fileSize/1MB, 2)) MB)" -ForegroundColor Magenta
        } else {
            Write-Host "❌ Legacy file missing: $file" -ForegroundColor Red
            $hasLegacyFiles = $false
        }
    }
    
    if (-not $hasLegacyFiles) {
        Write-Host "❌ No complete set of vector files found (enhanced or legacy)" -ForegroundColor Red
        Write-Host "💡 Run: .\update_vectors.ps1 to copy vector files" -ForegroundColor Yellow
        exit 1
    }
}

if ($hasEnhancedFiles) {
    Write-Host "✅ Using Enhanced RAG System" -ForegroundColor Green
    $systemType = "Enhanced"
} else {
    Write-Host "✅ Using Legacy RAG System" -ForegroundColor Magenta
    $systemType = "Legacy"
}

# Using Application Default Credentials - no key file needed
Write-Host "✅ Using Application Default Credentials" -ForegroundColor Green

# Verify critical Python files
Write-Host "🔍 Verifying critical Python files..." -ForegroundColor Yellow
$criticalFiles = @(
    "app/faiss_vector_service.py",
    "app/startup.py",
    "agent/chat_manager.py",
    "agent/retrieval.py",
    "api/routes_chat.py"
)

foreach ($file in $criticalFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Critical file not found: $file" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Found: $file" -ForegroundColor Green
}

# Quick check for class name in faiss_vector_service.py
Write-Host "🔍 Checking FAISS service class name..." -ForegroundColor Yellow
$faissContent = Get-Content "app/faiss_vector_service.py" -Raw
if ($faissContent -match "class\s+(\w+FAISSVectorService|LocalFAISSVectorService)") {
    $className = $matches[1]
    Write-Host "✅ Found FAISS class: $className" -ForegroundColor Green
    
    # Check if startup.py imports the correct class
    $startupContent = Get-Content "app/startup.py" -Raw
    if ($startupContent -match "from app.faiss_vector_service import $className") {
        Write-Host "✅ Startup imports correct class: $className" -ForegroundColor Green
    } else {
        # Check for alternative import patterns
        if ($startupContent -match "from app.faiss_vector_service import.*") {
            Write-Host "⚠️ Startup has FAISS import, but couldn't verify exact class" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Startup does NOT import FAISS service!" -ForegroundColor Red
            Write-Host "   Please check app/startup.py imports" -ForegroundColor Yellow
            exit 1
        }
    }
} else {
    Write-Host "⚠️ Could not find FAISS class definition" -ForegroundColor Yellow
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
        $content = Get-Content $file.Name -Raw
        $content = $content.Trim()
        if ($content -eq $file.Expected) {
            Write-Host "✅ Found: $($file.Name) ($($file.Description))" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $($file.Name) content mismatch:" -ForegroundColor Yellow
            Write-Host "   Found: '$content'" -ForegroundColor Gray
            Write-Host "   Expected: '$($file.Expected)'" -ForegroundColor Gray
        }
    }
}

# Generate a unique deployment ID for tracking
$deployId = "deploy-" + (Get-Date -Format "yyyyMMdd-HHmmss")
Write-Host "🏷️ Deployment ID: $deployId" -ForegroundColor Cyan
Write-Host "🔧 System Type: $systemType RAG" -ForegroundColor Cyan

# Clean any previous build artifacts
Write-Host "🧹 Cleaning previous build artifacts..." -ForegroundColor Yellow
if (Test-Path ".cloudbuild") {
    Remove-Item -Recurse -Force ".cloudbuild"
}

Write-Host "📦 Deploying with buildpack from source..." -ForegroundColor Yellow
Write-Host "   Using project: $ProjectId" -ForegroundColor Gray
Write-Host "   Deployment method: Cloud Buildpacks" -ForegroundColor Gray

# Enhanced environment variables
$envVars = "PROJECT_ID=$ProjectId,LOCATION=$Region,IS_LOCAL=false,LOCAL_VECTOR_FILES_PATH=app/vector-files,FAISS_INDEX_TYPE=IVF,CORS_ORIGINS=https://chatbot-frontend--ai-chatbot-472322.us-central1.app,DEBUG_MODE=true,LOG_QUERIES=false,EMBEDDING_QUANT=10,FIREBASE_STORAGE_BUCKET=ai-chatbot-472322.appspot.com"

if ($hasEnhancedFiles) {
    $envVars += ",CHUNK_SIZE_MIN=512,CHUNK_SIZE_MAX=1024,CHUNK_OVERLAP_PERCENT=10,ENABLE_LLM_CLASSIFICATION=true"
}

# Deploy to Cloud Run with buildpack from source
Write-Host "🌐 Deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host "   Service: $ServiceName" -ForegroundColor Gray
Write-Host "   Region: $Region" -ForegroundColor Gray
Write-Host "   Source: Current directory (.)" -ForegroundColor Gray
Write-Host "   System: $systemType RAG" -ForegroundColor Gray

# First, check if service exists
gcloud run services describe $ServiceName --region=$Region --project=$ProjectId 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "📝 Updating existing service..." -ForegroundColor Yellow
} else {
    Write-Host "📝 Creating new service..." -ForegroundColor Yellow
}

# Deploy with buildpack from source directory
gcloud run deploy $ServiceName `
    --source . `
    --region $Region `
    --allow-unauthenticated `
    --service-account "ai-agent-runner@$ProjectId.iam.gserviceaccount.com" `
    --set-env-vars $envVars `
    --memory 4Gi `
    --cpu 2 `
    --max-instances 10 `
    --timeout 300 `
    --platform managed `
    --project $ProjectId `
    --no-traffic

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Cloud Run deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ AI Agent Service deployed successfully with buildpack!" -ForegroundColor Green

# Get service URL
$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format "value(status.url)" --project $ProjectId
Write-Host "🔗 Service URL: $ServiceUrl" -ForegroundColor Cyan

# Now route traffic to the new revision
Write-Host "🔄 Routing traffic to new revision..." -ForegroundColor Yellow
gcloud run services update-traffic $ServiceName `
    --to-latest `
    --region $Region `
    --project $ProjectId

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Traffic routed to new revision" -ForegroundColor Green
} else {
    Write-Host "⚠️ Failed to route traffic automatically" -ForegroundColor Yellow
}

# Get the latest revision name
$latestRevision = gcloud run revisions list `
    --service=$ServiceName `
    --region=$Region `
    --project=$ProjectId `
    --limit=1 `
    --format="value(name)"

Write-Host "📌 Latest revision: $latestRevision" -ForegroundColor Cyan

# Wait for service to be ready
Write-Host "⏳ Waiting for service to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Test health endpoint
Write-Host "🧪 Testing health endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$ServiceUrl/health" -Method Get -TimeoutSec 30
    Write-Host "✅ Health check passed" -ForegroundColor Green
    Write-Host ($healthResponse | ConvertTo-Json -Depth 3) -ForegroundColor Gray
    
    # Check if FAISS service is loaded
    if ($healthResponse.services.faiss_service -eq $true) {
        Write-Host "✅ FAISS vector service is running" -ForegroundColor Green
    } else {
        Write-Host "⚠️ FAISS service not loaded - check logs" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "⚠️ Health check failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "🔍 Checking service logs..." -ForegroundColor Yellow
    & gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$ServiceName" --limit=20 --format='table(timestamp,severity,textPayload)' --project=$ProjectId
}

# Update .env file
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "AI_SERVICE_URL=.*") {
        $envContent = $envContent -replace "AI_SERVICE_URL=.*", "AI_SERVICE_URL=$ServiceUrl"
    } else {
        $envContent += "`nAI_SERVICE_URL=$ServiceUrl"
    }
    Set-Content ".env" $envContent
    Write-Host "📝 Updated .env with service URL" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Enhanced AI Agent Service buildpack deployment complete!" -ForegroundColor Green
Write-Host "🔗 Service URL: $ServiceUrl" -ForegroundColor Cyan
Write-Host "🏷️ Deployment ID: $deployId" -ForegroundColor Gray
Write-Host "📌 Revision: $latestRevision" -ForegroundColor Gray
Write-Host "🔧 System: $systemType RAG" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Buildpack Service Configuration:" -ForegroundColor Yellow
Write-Host "    - Deployment Method: Cloud Buildpacks" -ForegroundColor White
Write-Host "    - Python Runtime: 3.11 (from .python-version)" -ForegroundColor White
Write-Host "    - Process: web: python main.py (from Procfile)" -ForegroundColor White
Write-Host "    - RAG System: $systemType" -ForegroundColor White
Write-Host "    - Vector Files: app/vector-files/" -ForegroundColor White
Write-Host "    - Memory: 4GB" -ForegroundColor White
Write-Host "    - CPU: 2 cores" -ForegroundColor White
Write-Host "    - Max Instances: 10" -ForegroundColor White
Write-Host "    - Firebase Storage: ai-chatbot-472322.appspot.com" -ForegroundColor White

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test: python deployment/test_ai_service.py" -ForegroundColor White
Write-Host "2. Test images: Check Firebase Storage setup" -ForegroundColor White
Write-Host "3. Test chat: Run the test script above" -ForegroundColor White
Write-Host "4. Monitor: gcloud logging read 'resource.type=cloud_run_revision'" -ForegroundColor White