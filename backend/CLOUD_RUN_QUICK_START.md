# 🚀 Quick Start: Deploy FutureGolf to Google Cloud Run

This is a simplified guide to get your backend running on Google Cloud Run in under 15 minutes.

## 📋 Before You Start

You need:
1. A Google account
2. A credit card (for Google Cloud billing - you get $300 free credits)
3. Your computer's terminal/command line

## 🛠️ Step 1: Set Up Google Cloud (5 minutes)

1. **Create a Google Cloud Account**
   - Go to https://console.cloud.google.com
   - Click "Start Free" and follow the setup
   - You'll get $300 in free credits!

2. **Create a New Project**
   - In the Google Cloud Console, click the project dropdown (top bar)
   - Click "New Project"
   - Name it something like "futuregolf-backend"
   - Copy the Project ID (you'll need this!)

3. **Enable Billing**
   - Go to Billing in the left menu
   - Link your credit card (you won't be charged during free trial)

## 💻 Step 2: Install Google Cloud CLI (5 minutes)

### For macOS:
```bash
# If you have Homebrew installed:
brew install google-cloud-sdk

# If not, download from:
# https://cloud.google.com/sdk/docs/install-sdk#mac
```

### For Windows:
Download installer from: https://cloud.google.com/sdk/docs/install-sdk#windows

### For Linux:
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

## 🔑 Step 3: Prepare Your Backend (3 minutes)

1. **Open Terminal and Navigate to Backend**
   ```bash
   cd /Users/greg/Dev/work/NewCo/futuregolf/backend
   ```

2. **Set Your Project ID**
   ```bash
   # Replace 'your-project-id' with your actual project ID from Step 1
   export GCP_PROJECT_ID="your-project-id"
   ```

3. **Login to Google Cloud**
   ```bash
   gcloud auth login
   # This will open your browser - login with your Google account
   ```

## 🚀 Step 4: Deploy! (2 minutes)

Simply run the deployment script:

```bash
./deploy-to-cloud-run.sh
```

The script will:
- ✅ Set up everything automatically
- ✅ Upload your code
- ✅ Configure the database
- ✅ Deploy your backend
- ✅ Give you a URL to access your API

## ✨ That's It! You're Live!

After deployment, you'll see something like:
```
Your service is available at: https://futuregolf-backend-abc123-uc.a.run.app
```

Test it by visiting:
- `https://your-url/health` - Should show "healthy"
- `https://your-url/docs` - Your API documentation

## 🔧 Common Issues & Fixes

### "Permission Denied" Error
```bash
chmod +x deploy-to-cloud-run.sh
./deploy-to-cloud-run.sh
```

### "Project ID not set" Error
```bash
# Make sure to set your project ID
export GCP_PROJECT_ID="your-actual-project-id"
```

### "Billing account not linked" Error
- Go to https://console.cloud.google.com/billing
- Link a billing account to your project

### Can't find gcloud command
- Restart your terminal after installation
- Or run: `source ~/.bashrc` (Linux) or `source ~/.zshrc` (macOS)

## 📱 Connect Your Frontend

Update your React Native app to use the new backend URL:

1. In your frontend `.env` file:
   ```
   EXPO_PUBLIC_API_BASE_URL=https://your-cloud-run-url/api/v1
   ```

2. Restart your Expo app

## 💰 Cost Estimates

With Google Cloud Run, you only pay for what you use:
- **First 2 million requests/month**: FREE
- **First 360,000 GB-seconds memory**: FREE
- **First 180,000 vCPU-seconds**: FREE

For a typical startup app: **$0-$10/month**

## 🛡️ Security Notes

Your deployment automatically includes:
- ✅ HTTPS encryption
- ✅ Secure API key storage
- ✅ Protected database credentials
- ✅ DDoS protection

## 📊 View Logs & Monitor

See what's happening with your backend:

```bash
# View recent logs
gcloud run services logs read futuregolf-backend --limit 50

# Stream live logs
gcloud run services logs tail futuregolf-backend
```

Or use the Google Cloud Console:
1. Go to https://console.cloud.google.com
2. Navigate to Cloud Run
3. Click on your service
4. View logs, metrics, and more!

## 🔄 Update Your Deployment

Made changes? Redeploy in seconds:

```bash
./deploy-to-cloud-run.sh
```

## 🆘 Need Help?

- **Google Cloud Run Docs**: https://cloud.google.com/run/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Common Error Messages**: Check the logs with `gcloud run services logs read futuregolf-backend --limit 100`

## 🎉 Congratulations!

Your backend is now running on Google's global infrastructure with:
- Automatic scaling
- 99.95% uptime SLA
- Global CDN
- Built-in monitoring

Next steps:
1. Share your API URL with your team
2. Set up your custom domain (optional)
3. Configure monitoring alerts (optional)
4. Celebrate! 🎊