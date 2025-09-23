# Deployment Guide

This guide covers production deployment of the Universal Manual RAG Chat system to Google Cloud Platform and Firebase.

## Prerequisites

### Required Accounts & Tools
- Google Cloud Platform account with billing enabled
- Firebase project
- GitHub account (for CI/CD)
- Domain name (optional, for custom domains)

### Required CLI Tools
```bash
# Google Cloud CLI
curl https://sdk.cloud.google.com | bash
gcloud auth login

# Firebase CLI
npm install -g firebase-tools
firebase login

# GitHub CLI (optional)
# Windows: winget install GitHub.cli
# macOS: brew install gh
# Linux: See https://github.com/cli/cli#installation
```

## Environment Setup

### 1. Google Cloud Project Setup

```bash
# Set project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable texttospeech.googleapis.com
gcloud services enable speech.googleapis.com
gcloud services enable storage.googleapis.com
```

### 2. Service Account Creation

```bash
# Create service account for backend
gcloud iam service-accounts create ai-agent-service \
  --display-name="AI Agent Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:ai-agent-service@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:ai-agent-service@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create gcp-keys/ai-chatbot-service-account.json \
  --iam-account=ai-agent-service@$PROJECT_ID.iam.gserviceaccount.com
```

### 3. Firebase Project Setup

```bash
# Initialize Firebase in your project
firebase init

# Select features:
# - Hosting
# - Functions
# - Firestore
# - Storage

# Configure Firebase project
firebase use --add your-firebase-project-id
```

## Backend Deployment (Google Cloud Run)

### 1. Prepare Environment Variables

Create `.env` file in `chatbot_backend/`:

```bash
# chatbot_backend/.env
PROJECT_ID=your-project-id
LOCATION=us-central1
GENERATIVE_MODEL_NAME=gemini-2.5-flash
EMBEDDING_MODEL_NAME=text-embedding-004
DEFAULT_VOICE_NAME=en-US-Chirp3-HD-Leda
CORS_ORIGINS=https://your-frontend-domain.com,https://your-custom-domain.com
```

### 2. Deploy with Script

```bash
cd chatbot_backend

# Make deployment script executable
chmod +x deployment/deploy_ai_service.ps1

# Deploy (this will build and push to Cloud Run)
./deployment/deploy_ai_service.ps1
```

### 3. Manual Deployment Steps

If you prefer manual deployment:

```bash
# Build container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/ai-agent-service

# Deploy to Cloud Run
gcloud run deploy ai-agent-service \
  --image gcr.io/$PROJECT_ID/ai-agent-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1
```

### 4. Update Vector Files in Production

```bash
# After processing new manuals locally
./deployment/update_vectors.ps1

# Or manually
gsutil cp app/vector-files/* gs://your-bucket/vector-files/
```

## Frontend Deployment (Firebase)

### 1. Configure Firebase Hosting

Update `chatbot_frontend/firebase.json`:

```json
{
  "hosting": {
    "public": "build/web",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      }
    ]
  }
}
```

### 2. Update Backend URL

Update `chatbot_frontend/lib/services/ai_chat_service.dart`:

```dart
final String _backendBaseUrl = 'https://ai-agent-service-325296751367.us-central1.run.app';
```

### 3. Build and Deploy Flutter Web

```bash
cd chatbot_frontend

# Build for web
flutter build web --release

# Deploy to Firebase Hosting
firebase deploy --only hosting
```

### 4. Deploy Firebase Functions

```bash
cd chatbot_frontend/functions

# Install dependencies
npm install

# Deploy functions
firebase deploy --only functions
```

## Database Setup (Firestore)

### 1. Firestore Security Rules

Update `firestore.rules`:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Chat sessions
    match /chat_sessions/{sessionId} {
      allow read, write: if request.auth != null &&
        resource.data.userId == request.auth.uid;
    }

    // Public manual metadata (read-only)
    match /manuals/{manualId} {
      allow read: if true;
      allow write: if false;
    }
  }
}
```

### 2. Storage Rules

Update `storage.rules`:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Manual images (public read)
    match /ai_images/{allPaths=**} {
      allow read: if true;
      allow write: if false;
    }

    // User uploads (authenticated)
    match /user_uploads/{userId}/{allPaths=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### 3. Deploy Rules

```bash
firebase deploy --only firestore:rules,storage
```

## CI/CD Pipeline (GitHub Actions)

### 1. GitHub Secrets

Add these secrets to your GitHub repository:

```
GCP_PROJECT_ID: your-project-id
GCP_SA_KEY: (base64 encoded service account JSON)
FIREBASE_TOKEN: (firebase login:ci token)
```

### 2. Backend CI/CD

Create `.github/workflows/deploy-backend.yml`:

```yaml
name: Deploy Backend to Cloud Run

on:
  push:
    branches: [ main ]
    paths: [ 'chatbot_backend/**' ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Google Cloud CLI
      uses: google-github-actions/setup-gcloud@v1
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        export_default_credentials: true

    - name: Build and Deploy
      run: |
        cd chatbot_backend
        gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/ai-agent-service
        gcloud run deploy ai-agent-service \
          --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/ai-agent-service \
          --platform managed \
          --region us-central1 \
          --allow-unauthenticated
```

### 3. Frontend CI/CD

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy Frontend to Firebase

on:
  push:
    branches: [ main ]
    paths: [ 'chatbot_frontend/**' ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.x'

    - name: Build Flutter Web
      run: |
        cd chatbot_frontend
        flutter pub get
        flutter build web --release

    - name: Deploy to Firebase
      uses: FirebaseExtended/action-hosting-deploy@v0
      with:
        repoToken: '${{ secrets.GITHUB_TOKEN }}'
        firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
        projectId: your-firebase-project-id
```

## Domain Configuration

### 1. Custom Domain for Backend

```bash
# Map custom domain to Cloud Run
gcloud run domain-mappings create \
  --service ai-agent-service \
  --domain api.yourdomain.com \
  --region us-central1
```

### 2. Custom Domain for Frontend

```bash
# Add custom domain to Firebase Hosting
firebase hosting:channel:deploy production \
  --only hosting
```

## Monitoring & Logging

### 1. Cloud Logging

```bash
# View logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent-service' --limit=50

# Create log-based alerts
gcloud alpha logging sinks create error-sink \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/logs \
  --log-filter='severity>=ERROR'
```

### 2. Performance Monitoring

Enable Application Performance Monitoring in Firebase Console:
1. Go to Firebase Console → Performance
2. Enable Performance Monitoring
3. Add monitoring to Flutter app

### 3. Error Reporting

```bash
# Enable Error Reporting API
gcloud services enable clouderrorreporting.googleapis.com
```

## Security Configuration

### 1. CORS Configuration

Update backend CORS settings in `app/startup.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://your-firebase-app.web.app",
        "https://your-firebase-app.firebaseapp.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 2. API Authentication (Future)

Prepare for API key authentication:

```python
# In future versions
@app.middleware("http")
async def validate_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if not api_key or not validate_key(api_key):
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid API key"}
        )
    response = await call_next(request)
    return response
```

## Performance Optimization

### 1. Cloud Run Configuration

```bash
# Optimize for performance
gcloud run deploy ai-agent-service \
  --cpu 2 \
  --memory 4Gi \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80 \
  --timeout 300
```

### 2. CDN Configuration

Enable Cloud CDN for static assets:

```bash
# Create backend bucket
gsutil mb gs://$PROJECT_ID-static-assets

# Enable CDN
gcloud compute backend-buckets create static-backend \
  --gcs-bucket-name=$PROJECT_ID-static-assets
```

## Troubleshooting

### Common Issues

1. **Cold starts**: Set min-instances to 1
2. **Memory errors**: Increase Cloud Run memory allocation
3. **CORS errors**: Check allowed origins configuration
4. **Authentication failures**: Verify service account permissions

### Debug Commands

```bash
# Check Cloud Run logs
gcloud logging read 'resource.type=cloud_run_revision' --limit=20

# Test endpoints
curl https://your-backend.run.app/health
curl https://your-backend.run.app/debug/faiss-status

# Check Firebase deployment
firebase hosting:channel:list
firebase functions:log
```

## Scaling Considerations

### Auto-scaling Configuration

```bash
# Configure auto-scaling
gcloud run services update ai-agent-service \
  --min-instances=2 \
  --max-instances=100 \
  --concurrency=50
```

### Database Scaling

- Firestore automatically scales
- Consider sharding for high-volume applications
- Monitor read/write quotas

### Storage Scaling

- Firebase Storage automatically scales
- Consider CDN for global distribution
- Monitor bandwidth usage

## Cost Optimization

### Cloud Run Cost Optimization

- Use minimum necessary CPU/memory
- Set appropriate max-instances
- Monitor cold start frequency

### Firebase Cost Optimization

- Optimize Firestore queries
- Use storage compression
- Monitor bandwidth usage

### Monitoring Costs

```bash
# Set up billing alerts
gcloud alpha billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="Universal RAG Chat Budget" \
  --budget-amount=100USD
```