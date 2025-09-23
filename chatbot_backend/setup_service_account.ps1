# setup_service_account.ps1
param(
    [string]$ProjectId = "ai-chatbot-472322"
)

Write-Host "Setting up Cloud Run service account for project: $ProjectId" -ForegroundColor Green

# Create service account
Write-Host "Creating service account..." -ForegroundColor Yellow
gcloud iam service-accounts create ai-agent-runner `
    --description="Service account for AI Agent Cloud Run service" `
    --display-name="AI Agent Runner" `
    --project=$ProjectId

if ($LASTEXITCODE -ne 0) {
    Write-Host "Service account might already exist, continuing..." -ForegroundColor Yellow
}

# Grant necessary permissions
$serviceAccount = "ai-agent-runner@$ProjectId.iam.gserviceaccount.com"

Write-Host "Granting permissions to: $serviceAccount" -ForegroundColor Yellow

# AI Platform permissions for Gemini
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/aiplatform.user"

# Vertex AI permissions
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/ml.developer"

# Cloud Speech permissions
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/speech.client"

# Firebase Admin permissions
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/firebase.admin"

# Storage permissions for Firebase Storage
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/storage.admin"

# Logging permissions
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/logging.logWriter"

Write-Host "Service account setup complete!" -ForegroundColor Green
Write-Host "Service account email: $serviceAccount" -ForegroundColor Cyan