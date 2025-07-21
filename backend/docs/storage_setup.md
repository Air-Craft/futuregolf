# Google Cloud Storage Setup Guide

This guide will help you set up Google Cloud Storage for the FutureGolf project.

## Prerequisites

1. Google Cloud Platform account
2. Google Cloud SDK installed locally
3. Python 3.8+ with pip

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID (you'll need this later)

## Step 2: Enable Required APIs

Enable the following APIs in your project:
- Cloud Storage API
- Cloud CDN API (optional, for CDN integration)

```bash
gcloud services enable storage.googleapis.com
gcloud services enable compute.googleapis.com
```

## Step 3: Create Service Account

1. Go to IAM & Admin > Service Accounts
2. Click "Create Service Account"
3. Name: `futuregolf-storage-service`
4. Description: `Service account for FutureGolf video storage`
5. Click "Create and Continue"
6. Add roles:
   - Storage Admin
   - Storage Object Admin
7. Click "Done"

## Step 4: Generate Service Account Key

1. Click on the created service account
2. Go to "Keys" tab
3. Click "Add Key" > "Create New Key"
4. Choose JSON format
5. Download the key file
6. Store it securely (DO NOT commit to version control)

## Step 5: Install Dependencies

```bash
# Install storage-specific dependencies
pip install -r requirements_storage.txt

# Or install individual packages
pip install google-cloud-storage==2.20.0
pip install google-resumable-media==2.7.2
pip install google-auth==2.35.0
```

## Step 6: Configure Environment Variables

1. Copy `.env.example` to `.env`
2. Update the following variables:

```env
# Replace with your actual values
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account-key.json
GCS_BUCKET_NAME=futuregolf-videos-unique-name
GCS_BUCKET_LOCATION=us-central1
```

## Step 7: Run Setup Script

```bash
# Make the setup script executable
chmod +x setup_gcs.py

# Run the setup script
python setup_gcs.py
```

This script will:
- Create the storage bucket
- Configure CORS settings
- Set up lifecycle rules
- Create folder structure
- Test basic operations

## Step 8: Verify Setup

Check that everything is working:

```python
from services.storage_service import storage_service

# Test connection
result = await storage_service.get_file_metadata("videos/.placeholder")
print(f"Setup verification: {result}")
```

## Storage Structure

Your bucket will be organized as follows:

```
futuregolf-videos/
├── videos/
│   └── user_{user_id}/
│       └── video_{video_id}/
│           └── {unique_filename}.mp4
├── thumbnails/
│   └── user_{user_id}/
│       └── video_{video_id}/
│           └── thumbnail_{uuid}.jpg
├── processed/
│   └── user_{user_id}/
│       └── video_{video_id}/
│           └── processed_{type}_{uuid}.mp4
└── temp/
    └── {temporary_files}
```

## Security Considerations

1. **Service Account Key**: Never commit your service account key to version control
2. **Bucket Permissions**: Keep the bucket private, use signed URLs for access
3. **CORS**: Configure CORS only for your domain
4. **Lifecycle Rules**: Automatically clean up temporary files

## CDN Integration (Optional)

To enable CDN for faster video delivery:

1. Go to Cloud CDN in Google Cloud Console
2. Create a new CDN configuration
3. Set your bucket as the origin
4. Update `GCS_CDN_ENABLED=true` and `GCS_CDN_BASE_URL` in your `.env`

## Cost Optimization

1. **Storage Classes**: 
   - Use Standard for frequently accessed videos
   - Use Nearline for videos accessed monthly
   - Use Coldline for archived content

2. **Lifecycle Rules**:
   - Automatically delete temp files after 7 days
   - Archive old videos after 90 days

3. **Compression**: Consider compressing videos before upload

## Monitoring

Set up monitoring for:
- Storage usage
- Request counts
- Error rates
- Cost tracking

## Troubleshooting

### Common Issues

1. **Authentication Error**: Check service account key path and permissions
2. **Bucket Already Exists**: Choose a globally unique bucket name
3. **Permission Denied**: Ensure service account has correct roles
4. **Quota Exceeded**: Check your GCP quotas and limits

### Debug Commands

```bash
# Check authentication
gcloud auth application-default print-access-token

# List buckets
gsutil ls

# Check bucket details
gsutil ls -L gs://your-bucket-name
```

## Next Steps

1. Integrate with your video upload endpoints
2. Set up monitoring and alerting
3. Configure CDN for global distribution
4. Implement video processing pipeline
5. Add backup and disaster recovery

For more information, see the [Google Cloud Storage documentation](https://cloud.google.com/storage/docs).