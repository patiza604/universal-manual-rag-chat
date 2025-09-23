#!/bin/bash
# Bash deployment script (avoiding PowerShell syntax issues)
# Basic bash implementation
PROJECT_ID=${1:-"ai-chatbot-472322"}
REGION=${2:-"us-central1"}
SERVICE_NAME=${3:-"ai-agent-service"}

echo "🚀 Building and deploying Enhanced AI Agent Service..."
echo "📁 Current directory: $(pwd)"

# Check vector files
if [ ! -d "app/vector-files" ]; then
    echo "❌ Vector files directory not found: app/vector-files"
    exit 1
fi

echo "✅ Vector files directory found"

# Build with Cloud Build
echo "📦 Building image with Google Cloud Build..."

cat > cloudbuild_temp.yaml << EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '--no-cache',
      '-t', 'gcr.io/$PROJECT_ID/$SERVICE_NAME:latest',
      '.'
    ]
images:
  - 'gcr.io/$PROJECT_ID/$SERVICE_NAME:latest'
options:
  machineType: 'E2_HIGHCPU_8'
timeout: '1200s'
EOF

gcloud builds submit --config=cloudbuild_temp.yaml --project=$PROJECT_ID

if [ $? -ne 0 ]; then
    echo "❌ Cloud Build failed"
    rm -f cloudbuild_temp.yaml
    exit 1
fi

rm -f cloudbuild_temp.yaml
echo "✅ Image built successfully"

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."

ENV_VARS="PROJECT_ID=$PROJECT_ID,LOCATION=$REGION,IS_LOCAL=false,LOCAL_VECTOR_FILES_PATH=app/vector-files,DEBUG_MODE=true"

gcloud run deploy $SERVICE_NAME \
    --image "gcr.io/$PROJECT_ID/$SERVICE_NAME:latest" \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars $ENV_VARS \
    --memory 4Gi \
    --cpu 2 \
    --max-instances 10 \
    --timeout 300 \
    --platform managed \
    --project $PROJECT_ID

if [ $? -eq 0 ]; then
    echo "✅ AI Agent Service deployed successfully!"

    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format "value(status.url)" --project $PROJECT_ID)
    echo "🔗 Service URL: $SERVICE_URL"

    # Test health endpoint
    echo "🧪 Testing health endpoint..."
    sleep 10
    curl -f "$SERVICE_URL/health" || echo "⚠️ Health check failed"

else
    echo "❌ Cloud Run deployment failed"
    exit 1
fi