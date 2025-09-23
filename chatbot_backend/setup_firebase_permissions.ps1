# Setup Firebase Storage permissions for ai-chatbot-472322 project
# Run this script to create a service account and grant permissions

Write-Host "Setting up Firebase Storage permissions for ai-chatbot-472322..." -ForegroundColor Green

# Set project
Write-Host "Setting project to ai-chatbot-472322..."
gcloud config set project ai-chatbot-472322

# Create service account
$serviceAccountName = "firebase-storage-admin"
$serviceAccountEmail = "$serviceAccountName@ai-chatbot-472322.iam.gserviceaccount.com"

Write-Host "Creating service account: $serviceAccountEmail"
gcloud iam service-accounts create $serviceAccountName `
    --display-name="Firebase Storage Admin for ChatBot" `
    --description="Service account for Firebase Storage access in ChatBot application"

# Grant necessary roles
Write-Host "Granting Firebase Admin role..."
gcloud projects add-iam-policy-binding ai-chatbot-472322 `
    --member="serviceAccount:$serviceAccountEmail" `
    --role="roles/firebase.admin"

Write-Host "Granting Storage Admin role..."
gcloud projects add-iam-policy-binding ai-chatbot-472322 `
    --member="serviceAccount:$serviceAccountEmail" `
    --role="roles/storage.admin"

Write-Host "Granting Storage Object Admin role..."
gcloud projects add-iam-policy-binding ai-chatbot-472322 `
    --member="serviceAccount:$serviceAccountEmail" `
    --role="roles/storage.objectAdmin"

# Create and download key
$keyFile = "gcp-keys/ai-chatbot-472322-firebase-storage.json"
Write-Host "Creating service account key: $keyFile"

if (!(Test-Path "gcp-keys")) {
    New-Item -ItemType Directory -Path "gcp-keys"
}

gcloud iam service-accounts keys create $keyFile `
    --iam-account=$serviceAccountEmail

Write-Host "Service account key created: $keyFile" -ForegroundColor Green

# Test the bucket access
Write-Host "Testing bucket access..."
$env:GOOGLE_APPLICATION_CREDENTIALS = $keyFile
gsutil ls gs://ai-chatbot-472322.firebasestorage.app/

Write-Host "Setup complete! You can now use the service account key for image uploads." -ForegroundColor Green