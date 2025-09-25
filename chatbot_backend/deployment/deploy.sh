#!/bin/bash
# Bash deployment script using buildpack deployment
# Deploys directly from source using Cloud Run buildpacks
PROJECT_ID=${1:-"ai-chatbot-472322"}
REGION=${2:-"us-central1"}
SERVICE_NAME=${3:-"ai-agent-service"}

echo "🚀 Deploying Enhanced AI Agent Service using buildpacks..."
echo "📁 Current directory: $(pwd)"

# Check vector files
if [ ! -d "app/vector-files" ]; then
    echo "❌ Vector files directory not found: app/vector-files"
    exit 1
fi

echo "✅ Vector files directory found"

# Deploy to Cloud Run using buildpack deployment
echo "📦 Building and deploying from source with buildpacks..."

ENV_VARS="PROJECT_ID=$PROJECT_ID,LOCATION=$REGION,IS_LOCAL=false,LOCAL_VECTOR_FILES_PATH=app/vector-files,DEBUG_MODE=true"

gcloud run deploy $SERVICE_NAME \
    --source . \
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
    echo "✅ AI Agent Service deployed successfully using buildpacks!"

    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format "value(status.url)" --project $PROJECT_ID)
    echo "🔗 Service URL: $SERVICE_URL"

    # Test health endpoint
    echo "🧪 Testing health endpoint..."
    sleep 10
    curl -f "$SERVICE_URL/health" || echo "⚠️ Health check failed"

else
    echo "❌ Buildpack deployment failed"
    exit 1
fi