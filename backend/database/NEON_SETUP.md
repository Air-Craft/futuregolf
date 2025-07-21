# Neon PostgreSQL Setup for FutureGolf

This guide provides step-by-step instructions for setting up a Neon PostgreSQL database for the FutureGolf application.

## Prerequisites

- A Neon account (free tier available)
- Python 3.8+ installed
- The FutureGolf backend code

## Step 1: Create Neon Account and Database

### 1.1 Sign up for Neon
1. Go to [neon.tech](https://neon.tech)
2. Click "Sign up" and create an account using GitHub, Google, or email
3. Complete the email verification if required

### 1.2 Create a New Project
1. After logging in, click "Create Project"
2. Choose a project name: `futuregolf-production` (or your preferred name)
3. Select your preferred region (choose closest to your users)
4. Click "Create project"

### 1.3 Get Database Connection Details
1. In your project dashboard, click on the "Connection Details" tab
2. Copy the connection string (it will look like):
   ```
   postgresql://username:password@ep-xxx-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
3. Keep this connection string secure - you'll need it for configuration

## Step 2: Configure Environment Variables

### 2.1 Create Production Environment File
1. Navigate to your backend directory:
   ```bash
   cd /Users/brian/Tech/Code/futuregolf/backend
   ```

2. Copy the Neon environment template:
   ```bash
   cp .env.neon .env.production
   ```

3. Edit the `.env.production` file:
   ```bash
   nano .env.production
   ```

### 2.2 Update Database Configuration
Replace the placeholder values in `.env.production`:

```bash
# Replace with your actual Neon connection string
DATABASE_URL=postgresql://your_username:your_password@your_host.neon.tech:5432/your_database?sslmode=require

# Neon-optimized settings (keep these as-is)
SQL_ECHO=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Update these with your production values
SECRET_KEY=your-super-secret-key-for-production
ENVIRONMENT=production
DEBUG=false

# Update with your frontend domain
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

## Step 3: Initialize the Database

### 3.1 Install Dependencies
```bash
pip install -r requirements.txt
```

### 3.2 Test Database Connection
```bash
python -m database.init_db --check
```

If successful, you should see: "Database connection successful!"

### 3.3 Initialize Database Tables
```bash
python -m database.init_db --init
```

This will:
- Create all required tables
- Set up indexes for performance
- Create PostgreSQL extensions

### 3.4 Verify Database Setup
```bash
python -m database.init_db --info
```

This will show you all created tables and their structure.

## Step 4: Run Database Tests

### 4.1 Run Full Test Suite
```bash
python -m database.test_db --test all
```

### 4.2 Run Specific Tests
```bash
# Test just the connection
python -m database.test_db --test connection

# Test CRUD operations
python -m database.test_db --test user
python -m database.test_db --test video
python -m database.test_db --test analysis
```

## Step 5: Set Up Database Migrations

### 5.1 Create Initial Migration
```bash
python -m database.migrations --initial
```

### 5.2 Check Migration Status
```bash
python -m database.migrations --status
```

## Step 6: Production Deployment

### 6.1 Environment Variables for Production
Set these environment variables in your production environment:

```bash
export DATABASE_URL="your_neon_connection_string"
export SECRET_KEY="your_production_secret_key"
export ENVIRONMENT="production"
export DEBUG="false"
```

### 6.2 Health Check Endpoint
You can create a health check endpoint in your FastAPI app:

```python
from database.utils import check_database_health

@app.get("/health/database")
async def database_health():
    health = check_database_health()
    if health["connection"]:
        return {"status": "healthy", "details": health}
    else:
        raise HTTPException(status_code=503, detail="Database unhealthy")
```

## Step 7: Monitoring and Maintenance

### 7.1 Monitor Database Usage
- Check your Neon dashboard regularly for usage statistics
- Monitor connection counts and query performance

### 7.2 Regular Maintenance
```bash
# Check database health
python -c "from database.utils import check_database_health; print(check_database_health())"

# Get table sizes
python -c "from database.utils import get_db_session, DatabaseHealth; db = get_db_session().__enter__(); print(DatabaseHealth.get_table_sizes(db))"
```

## Troubleshooting

### Common Issues

#### 1. Connection Timeout
If you get connection timeouts:
- Check your DATABASE_URL is correct
- Verify your IP is not blocked
- Try increasing connection timeout in `.env.production`:
  ```
  DB_POOL_TIMEOUT=60
  ```

#### 2. SSL Certificate Issues
If you get SSL errors:
- Ensure your connection string includes `?sslmode=require`
- Update your connection string to include the endpoint parameter if needed

#### 3. Pool Connection Issues
For serverless deployments, add to your environment:
```
USE_NULL_POOL=true
```

#### 4. Performance Issues
- Monitor your queries with `SQL_ECHO=true` in development
- Check the Neon dashboard for slow queries
- Consider upgrading your Neon plan for better performance

### Getting Help

- Check the Neon documentation: https://neon.tech/docs
- Review the logs: `python -m database.init_db --check` for connection issues
- Run the test suite: `python -m database.test_db --test all`

## Security Best Practices

1. **Never commit** your `.env.production` file to version control
2. **Use strong passwords** for your database user
3. **Regularly rotate** your SECRET_KEY
4. **Monitor access logs** in your Neon dashboard
5. **Use environment variables** for all secrets in production

## Database Schema

The following tables will be created:

- `users` - User accounts and authentication
- `videos` - Video uploads and metadata
- `video_analyses` - AI analysis results
- `subscriptions` - User subscription information
- `payments` - Payment records
- `usage_records` - Usage tracking
- `schema_migrations` - Database migration history

## Performance Optimization

The database configuration includes several optimizations for Neon:

1. **Connection Pooling**: Optimized pool size for Neon's connection limits
2. **SSL Configuration**: Proper SSL settings for secure connections
3. **Timeout Settings**: Appropriate timeouts for cloud hosting
4. **Indexes**: Performance indexes on frequently queried columns
5. **JIT Disabled**: Better cold start performance

## Backup and Recovery

Neon provides automatic backups, but you can also:

1. **Export data** using pg_dump:
   ```bash
   pg_dump "your_neon_connection_string" > backup.sql
   ```

2. **Monitor backups** in your Neon dashboard
3. **Test recovery procedures** regularly

## Cost Management

To manage costs on Neon:

1. **Monitor usage** in the Neon dashboard
2. **Set up alerts** for usage thresholds
3. **Optimize queries** to reduce compute usage
4. **Consider upgrading** to higher tiers for better performance per dollar

## Next Steps

After completing this setup:

1. Configure your FastAPI application to use the database
2. Set up your frontend to connect to the backend
3. Configure authentication and authorization
4. Set up monitoring and logging
5. Plan for scaling as your user base grows

## Support

For issues specific to this setup:
- Check the database logs: `python -m database.test_db --test connection`
- Review the Neon dashboard for errors
- Run the health check: `python -c "from database.utils import check_database_health; print(check_database_health())"`