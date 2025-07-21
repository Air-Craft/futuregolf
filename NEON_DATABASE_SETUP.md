# Neon Database Setup Guide

## Prerequisites
- ✅ Neon MCP configured in `.mcp.json`
- ✅ GCS setup completed with bucket `fg-video`
- ⚠️ Claude Desktop needs to be restarted to activate MCP

## Option 1: Using Neon MCP (After Claude Restart)

Once you restart Claude Desktop, you'll have access to Neon MCP tools. Use them to:

1. **Create a new Neon project** (if not already created)
2. **Create a database** named `futuregolf`
3. **Get the connection string** which will look like:
   ```
   postgresql://username:password@host.neon.tech:5432/futuregolf?sslmode=require
   ```

## Option 2: Manual Setup via Neon Console

1. **Go to [Neon Console](https://console.neon.tech)**

2. **Create a new project**:
   - Project name: `futuregolf`
   - Region: Choose closest to you
   - PostgreSQL version: 16 (latest)

3. **Get your connection string**:
   - Go to Dashboard → Connection Details
   - Copy the connection string
   - Make sure it includes `?sslmode=require`

4. **Update your `.env` file**:
   ```bash
   DATABASE_URL=postgresql://[user]:[password]@[host].neon.tech:5432/futuregolf?sslmode=require
   ```

## Initialize the Database

Once you have the connection string:

1. **Update the `.env` file**:
   ```bash
   cd backend
   # Edit .env and replace the DATABASE_URL line with your actual connection string
   ```

2. **Run the setup script**:
   ```bash
   cd backend
   source venv/bin/activate
   python setup_neon_database.py
   ```

3. **Verify the setup**:
   The script will:
   - Test the connection
   - Create all required tables
   - List created tables
   - Optionally create sample data

## Database Schema

The following tables will be created:

- **users** - User accounts and authentication
- **videos** - Video metadata and storage info
- **video_analyses** - AI analysis results (with JSONB)
- **subscriptions** - User subscription management
- **payments** - Payment records
- **usage_records** - Usage tracking

## Testing the Database

After setup, test the database:

```bash
# Start the FastAPI server
python start_server.py

# Access API docs
open http://localhost:8000/docs
```

## Troubleshooting

### Connection Issues
- Ensure `?sslmode=require` is in your connection string
- Check that your IP is allowed (Neon allows all IPs by default)
- Verify the database name matches

### Permission Issues
- Ensure your database user has full permissions
- The default Neon user should have all necessary permissions

### MCP Issues
- Make sure Claude Desktop is fully restarted
- Check that `.mcp.json` is in the project root
- Try the manual setup if MCP isn't working

## Next Steps

Once the database is set up:
1. ✅ All Phase 1 infrastructure is complete
2. 🚀 Ready to start Phase 2 - Core UI Components
3. 📱 Begin building the React Native UI

## Quick Test

```python
# Test your connection quickly
cd backend
source venv/bin/activate
python -c "
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
print('✅ Connection successful!' if engine else '❌ Connection failed')
"
```