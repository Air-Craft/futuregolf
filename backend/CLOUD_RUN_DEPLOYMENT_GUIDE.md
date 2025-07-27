# 🚀 Google Cloud Run Deployment Guide for FutureGolf Backend

This guide provides step-by-step instructions for deploying the FutureGolf FastAPI backend to Google Cloud Run.

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Environment Configuration](#environment-configuration)
4. [Deployment Options](#deployment-options)
5. [Post-Deployment Configuration](#post-deployment-configuration)
6. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
7. [Cost Optimization](#cost-optimization)
8. [Security Best Practices](#security-best-practices)

## Prerequisites

### 1. Google Cloud Account
- Create a Google Cloud account at https://console.cloud.google.com
- Set up billing (required for Cloud Run)
- Create a new project or use an existing one

### 2. Install Required Tools
```bash
# Install Google Cloud CLI (macOS)
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install

# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Verify installations
gcloud version
docker --version
```

### 3. Authenticate with Google Cloud
```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID (replace with your actual project ID)
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID
```

## Initial Setup

### 1. Enable Required APIs
```bash
# Enable all necessary Google Cloud APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable storage.googleapis.com
```

### 2. Create a Service Account (Optional but Recommended)
```bash
# Create a service account for Cloud Run
gcloud iam service-accounts create futuregolf-backend \
    --display-name="FutureGolf Backend Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:futuregolf-backend@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:futuregolf-backend@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:futuregolf-backend@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Environment Configuration

### 1. Prepare Your Secrets

The application uses several API keys and credentials that need to be securely stored:

```bash
# Navigate to backend directory
cd backend

# Create secrets in Google Secret Manager
# Database URL
echo -n "your-database-url" | gcloud secrets create database-url --data-file=-

# OpenAI API Key
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# Gemini API Key
echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-

# ElevenLabs API Key (if used)
echo -n "your-elevenlabs-api-key" | gcloud secrets create elevenlabs-api-key --data-file=-

# GCS Credentials
gcloud secrets create gcs-credentials --data-file=gcs-credential.json
```

### 2. Verify Your GCS Bucket
```bash
# Check if your bucket exists
gsutil ls gs://fg-video

# If not, create it
gsutil mb -p $GCP_PROJECT_ID -l us-central1 gs://fg-video

# Set bucket permissions
gsutil iam ch allUsers:objectViewer gs://fg-video
```

## Deployment Options

### Option 1: Automated Deployment Script (Recommended)

Use the provided deployment script for a one-command deployment:

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"

# Run the deployment script
./deploy-to-cloud-run.sh
```

The script will:
- Verify your Google Cloud setup
- Create/update all necessary secrets
- Build and push the Docker image
- Deploy to Cloud Run with proper configuration
- Output your service URL

### Option 2: Manual Deployment

If you prefer manual control, follow these steps:

#### Step 1: Build Docker Image
```bash
# Build the image
docker build -t gcr.io/$GCP_PROJECT_ID/futuregolf-backend:latest .

# Configure Docker for GCR
gcloud auth configure-docker

# Push the image
docker push gcr.io/$GCP_PROJECT_ID/futuregolf-backend:latest
```

#### Step 2: Deploy to Cloud Run
```bash
gcloud run deploy futuregolf-backend \
    --image gcr.io/$GCP_PROJECT_ID/futuregolf-backend:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 100 \
    --max-instances 10 \
    --min-instances 1 \
    --port 8080 \
    --set-env-vars "GCS_PROJECT_ID=$GCP_PROJECT_ID,GCS_BUCKET_NAME=fg-video" \
    --set-secrets "DATABASE_URL=database-url:latest" \
    --set-secrets "OPENAI_API_KEY=openai-api-key:latest" \
    --set-secrets "GEMINI_API_KEY=gemini-api-key:latest" \
    --set-secrets "ELEVENLABS_API_KEY=elevenlabs-api-key:latest" \
    --set-secrets "/app/gcs-credential.json=gcs-credentials:latest"
```

### Option 3: Continuous Deployment with Cloud Build

Set up automatic deployments on git push:

```bash
# Connect your GitHub repository
gcloud builds connect create github \
    --repo-owner=YourGitHubUsername \
    --repo-name=futuregolf

# Create a build trigger
gcloud builds triggers create github \
    --repo-owner=YourGitHubUsername \
    --repo-name=futuregolf \
    --branch-pattern="^main$" \
    --build-config=backend/cloudbuild.yaml
```

## Post-Deployment Configuration

### 1. Update CORS Origins

After deployment, update CORS to allow your frontend:

```bash
# Get your Cloud Run service URL
SERVICE_URL=$(gcloud run services describe futuregolf-backend \
    --region us-central1 --format 'value(status.url)')

# Update CORS origins (replace with your frontend URLs)
gcloud run services update futuregolf-backend \
    --region us-central1 \
    --update-env-vars CORS_ORIGINS="https://your-frontend-domain.com,https://www.your-frontend-domain.com"
```

### 2. Set Up Custom Domain (Optional)

```bash
# Verify domain ownership
gcloud domains verify your-domain.com

# Map domain to Cloud Run service
gcloud run domain-mappings create \
    --service futuregolf-backend \
    --domain api.your-domain.com \
    --region us-central1
```

### 3. Configure Cloud CDN (Optional, for better performance)

```bash
# Create a backend service
gcloud compute backend-services create futuregolf-cdn-backend \
    --global \
    --enable-cdn \
    --cache-mode=CACHE_ALL_STATIC

# Connect to Cloud Run
gcloud compute backend-services add-backend futuregolf-cdn-backend \
    --global \
    --network-endpoint-group-zone=us-central1 \
    --network-endpoint-group=futuregolf-backend-neg
```

## Monitoring and Troubleshooting

### View Logs
```bash
# Stream logs in real-time
gcloud run services logs tail futuregolf-backend --region us-central1

# View recent logs
gcloud run services logs read futuregolf-backend --region us-central1 --limit 50

# Filter logs by severity
gcloud run services logs read futuregolf-backend \
    --region us-central1 \
    --filter "severity>=ERROR"
```

### Monitor Performance
```bash
# View metrics in Cloud Console
echo "https://console.cloud.google.com/run/detail/us-central1/futuregolf-backend/metrics?project=$GCP_PROJECT_ID"

# Set up alerts
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_CHANNEL_ID \
    --display-name="High Error Rate Alert" \
    --condition-display-name="Error rate > 5%" \
    --condition-type=METRIC_THRESHOLD \
    --condition-metric-type=run.googleapis.com/request_count \
    --condition-metric-filter='resource.type="cloud_run_revision" AND metric.response_code_class="5xx"'
```

### Common Issues and Solutions

#### 1. Memory Issues
If you see "Memory limit exceeded" errors:
```bash
# Increase memory allocation
gcloud run services update futuregolf-backend \
    --region us-central1 \
    --memory 4Gi
```

#### 2. Cold Start Issues
To reduce cold starts:
```bash
# Keep minimum instances warm
gcloud run services update futuregolf-backend \
    --region us-central1 \
    --min-instances 2
```

#### 3. Database Connection Issues
- Verify DATABASE_URL secret is correctly set
- Check if database allows connections from Google Cloud IPs
- For Neon, ensure you're using the pooled connection string

#### 4. Video Processing Timeouts
For long video processing:
```bash
# Increase timeout (max 60 minutes)
gcloud run services update futuregolf-backend \
    --region us-central1 \
    --timeout 3600
```

## Cost Optimization

### 1. Resource Optimization
```bash
# For development/testing, use minimal resources
gcloud run services update futuregolf-backend \
    --region us-central1 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 2 \
    --min-instances 0
```

### 2. Set Up Budget Alerts
```bash
# Create a budget with alerts
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT_ID \
    --display-name="FutureGolf Monthly Budget" \
    --budget-amount=100 \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100
```

### 3. Monitor Costs
```bash
# View current month costs
gcloud billing accounts list
gcloud billing projects describe $GCP_PROJECT_ID
```

## Security Best Practices

### 1. Enable Security Scanning
```bash
# Enable vulnerability scanning for containers
gcloud container images scan IMAGE_URL
```

### 2. Set Up VPC Connector (for private resources)
```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create futuregolf-connector \
    --region us-central1 \
    --subnet futuregolf-subnet \
    --subnet-project $GCP_PROJECT_ID

# Update Cloud Run service
gcloud run services update futuregolf-backend \
    --region us-central1 \
    --vpc-connector futuregolf-connector
```

### 3. Enable Cloud Armor (DDoS protection)
```bash
# Create security policy
gcloud compute security-policies create futuregolf-policy \
    --description "FutureGolf API security policy"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
    --security-policy futuregolf-policy \
    --expression "true" \
    --action "rate-based-ban" \
    --rate-limit-threshold-count 100 \
    --rate-limit-threshold-interval-sec 60 \
    --ban-duration-sec 300
```

### 4. Regular Updates
```bash
# Update base image and dependencies regularly
docker build --pull -t gcr.io/$GCP_PROJECT_ID/futuregolf-backend:latest .
docker push gcr.io/$GCP_PROJECT_ID/futuregolf-backend:latest

# Redeploy
gcloud run services update futuregolf-backend \
    --region us-central1 \
    --image gcr.io/$GCP_PROJECT_ID/futuregolf-backend:latest
```

## Testing Your Deployment

After deployment, test your API:

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe futuregolf-backend \
    --region us-central1 --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test API configuration
curl $SERVICE_URL/api/v1/auth/config

# Test with httpie (if installed)
http $SERVICE_URL/health
```

## Rollback Procedure

If something goes wrong:

```bash
# List revisions
gcloud run revisions list --service futuregolf-backend --region us-central1

# Rollback to previous revision
gcloud run services update-traffic futuregolf-backend \
    --region us-central1 \
    --to-revisions PREVIOUS_REVISION_NAME=100
```

## Next Steps

1. **Set up monitoring dashboards** in Google Cloud Console
2. **Configure alerts** for errors and performance issues
3. **Set up CI/CD** with Cloud Build for automatic deployments
4. **Implement staging environment** for testing
5. **Configure backup strategies** for your database
6. **Set up log exports** to BigQuery for analysis

## Support

For issues specific to:
- **Cloud Run**: https://cloud.google.com/run/docs
- **FastAPI**: https://fastapi.tiangolo.com/
- **Docker**: https://docs.docker.com/

Remember to regularly review and update your deployment for security patches and performance improvements!