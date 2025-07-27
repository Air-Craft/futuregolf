# Backend Deployment Guide

## Automatic Deployment (GitHub Actions)

The backend automatically deploys to Google Cloud Run when changes are pushed to the `main` branch in the `backend/` directory.

### One-Time Setup (Already Done)

1. **Service Account Creation**
   ```bash
   gcloud iam service-accounts create github-actions-deploy \
     --display-name="GitHub Actions Deploy"
   ```

2. **Grant Permissions**
   ```bash
   gcloud projects add-iam-policy-binding golf-swing-analysis-467208 \
     --member="serviceAccount:github-actions-deploy@golf-swing-analysis-467208.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding golf-swing-analysis-467208 \
     --member="serviceAccount:github-actions-deploy@golf-swing-analysis-467208.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   
   gcloud projects add-iam-policy-binding golf-swing-analysis-467208 \
     --member="serviceAccount:github-actions-deploy@golf-swing-analysis-467208.iam.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser"
   ```

3. **Create Service Account Key**
   ```bash
   gcloud iam service-accounts keys create github-deploy-key.json \
     --iam-account=github-actions-deploy@golf-swing-analysis-467208.iam.gserviceaccount.com
   ```

4. **Add to GitHub Secrets**
   - Go to GitHub repo settings → Secrets and variables → Actions
   - Create new secret: `GCP_SA_KEY`
   - Paste the contents of `github-deploy-key.json`

## How It Works

1. **Push to main branch** → Any changes in `backend/` directory
2. **GitHub Actions triggered** → Builds Docker image
3. **Pushes to Container Registry** → Tagged with commit SHA
4. **Deploys to Cloud Run** → Updates the service

## Manual Deployment (If Needed)

### Prerequisites
- Google Cloud SDK installed
- Authenticated: `gcloud auth login`
- Docker installed

### Deploy Command
```bash
cd backend
./deploy-to-cloud-run.sh
```

## Environment Variables

These are automatically configured in Cloud Run:
- `HOST=0.0.0.0`
- `GCS_PROJECT_ID=golf-swing-analysis-467208`
- `GCS_BUCKET_NAME=golf-swing-analysis-467208-videos`
- `GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcs-credentials/gcs-credential.json`

## Secrets

These are stored in Google Secret Manager:
- `database-url` - PostgreSQL connection string
- `openai-api-key` - OpenAI API key
- `gemini-api-key` - Google Gemini API key
- `gcs-credentials` - Google Cloud Storage credentials

## Monitoring

- **Logs**: `gcloud run logs read --service=futuregolf-backend --region=us-central1`
- **Console**: https://console.cloud.google.com/run/detail/us-central1/futuregolf-backend

## Rollback

To rollback to a previous version:
```bash
gcloud run services update-traffic futuregolf-backend \
  --region=us-central1 \
  --to-revisions=PREVIOUS_REVISION_NAME=100
```