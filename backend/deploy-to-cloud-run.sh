#!/bin/bash

# FutureGolf Backend - Google Cloud Run Deployment Script
# This script handles the complete deployment process

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-""}
REGION=${GCP_REGION:-"us-central1"}
SERVICE_NAME="futuregolf-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Function to print colored output
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    print_error "PROJECT_ID is not set!"
    echo "Please run: export GCP_PROJECT_ID=your-project-id"
    echo "Or edit this script and set PROJECT_ID directly"
    exit 1
fi

# Step 1: Verify gcloud is installed and authenticated
print_step "Checking Google Cloud CLI setup..."
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed!"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_warning "Not authenticated with gcloud"
    print_step "Authenticating with Google Cloud..."
    gcloud auth login
fi

# Set project
print_step "Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Step 2: Enable required APIs
print_step "Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable storage.googleapis.com
print_success "APIs enabled"

# Step 3: Create secrets in Secret Manager
print_step "Setting up secrets in Secret Manager..."

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if gcloud secrets describe ${secret_name} --project=${PROJECT_ID} &>/dev/null; then
        print_warning "Secret ${secret_name} already exists, updating..."
        echo -n "${secret_value}" | gcloud secrets versions add ${secret_name} --data-file=-
    else
        print_step "Creating secret ${secret_name}..."
        echo -n "${secret_value}" | gcloud secrets create ${secret_name} --data-file=- --replication-policy="automatic"
    fi
}

# Read .env file and create secrets
if [ -f ".env" ]; then
    print_step "Reading environment variables from .env file..."
    
    # Create secrets for sensitive data
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z $key ]] && continue
        
        # Remove quotes from value
        value=$(echo $value | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
        
        case $key in
            DATABASE_URL)
                create_or_update_secret "database-url" "$value"
                ;;
            OPENAI_API_KEY)
                create_or_update_secret "openai-api-key" "$value"
                ;;
            GEMINI_API_KEY)
                create_or_update_secret "gemini-api-key" "$value"
                ;;
            ELEVENLABS_API_KEY)
                create_or_update_secret "elevenlabs-api-key" "$value"
                ;;
        esac
    done < .env
    print_success "Secrets created/updated"
else
    print_error ".env file not found!"
    exit 1
fi

# Step 4: Upload GCS credentials as a secret
if [ -f "gcs-credential.json" ]; then
    print_step "Uploading GCS credentials to Secret Manager..."
    gcloud secrets create gcs-credentials --data-file=gcs-credential.json --replication-policy="automatic" 2>/dev/null || \
    gcloud secrets versions add gcs-credentials --data-file=gcs-credential.json
    print_success "GCS credentials uploaded"
else
    print_error "gcs-credential.json not found!"
    exit 1
fi

# Step 5: Build and push Docker image
print_step "Building Docker image..."
docker build --platform linux/amd64 -t ${IMAGE_NAME}:latest .
print_success "Docker image built"

print_step "Configuring Docker for Google Container Registry..."
gcloud auth configure-docker

print_step "Pushing Docker image to Container Registry..."
docker push ${IMAGE_NAME}:latest
print_success "Docker image pushed"

# Step 6: Deploy to Cloud Run
print_step "Deploying to Cloud Run..."

# Grant Cloud Run access to secrets
print_step "Granting Cloud Run access to secrets..."
SERVICE_ACCOUNT="${PROJECT_ID}-compute@developer.gserviceaccount.com"

for secret in database-url openai-api-key gemini-api-key elevenlabs-api-key gcs-credentials; do
    gcloud secrets add-iam-policy-binding ${secret} \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor" &>/dev/null || true
done

# Deploy with environment variables and mounted secrets
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 100 \
    --max-instances 10 \
    --min-instances 1 \
    --port 8080 \
    --set-env-vars "GCS_PROJECT_ID=${PROJECT_ID},GCS_BUCKET_NAME=fg-video,CORS_ORIGINS=*" \
    --set-secrets "DATABASE_URL=database-url:latest" \
    --set-secrets "OPENAI_API_KEY=openai-api-key:latest" \
    --set-secrets "GEMINI_API_KEY=gemini-api-key:latest" \
    --set-secrets "ELEVENLABS_API_KEY=elevenlabs-api-key:latest" \
    --set-secrets "/app/gcs-credential.json=gcs-credentials:latest"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

print_success "Deployment complete!"
echo ""
echo "Your service is available at: ${SERVICE_URL}"
echo ""
echo "Test your deployment:"
echo "  curl ${SERVICE_URL}/health"
echo "  curl ${SERVICE_URL}/api/v1/auth/config"
echo ""
echo "To view logs:"
echo "  gcloud run services logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "To update CORS origins for your frontend:"
echo "  gcloud run services update ${SERVICE_NAME} --region ${REGION} --update-env-vars CORS_ORIGINS=<your-frontend-url>"