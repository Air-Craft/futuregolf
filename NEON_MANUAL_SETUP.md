# Quick Neon Database Setup (Manual)

Since MCP tools aren't loading, here's the quick manual setup:

## 1. Create Neon Database

Go to [console.neon.tech](https://console.neon.tech) and:
1. Sign in / Create account
2. Click "Create Project"
3. Name it: `futuregolf`
4. Select region closest to you
5. Click "Create Project"

## 2. Get Connection String

In Neon Console:
1. Go to your project dashboard
2. Find "Connection Details" section
3. Copy the connection string (it will look like):
   ```
   postgresql://username:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```

## 3. Update Your .env

```bash
cd backend
# Edit .env file and replace the DATABASE_URL line
```

## 4. Run Setup

```bash
cd backend
source venv/bin/activate
python setup_neon_database.py
```

That's it! Takes about 2 minutes total.

## Why MCP Isn't Working

MCP in Claude Code is still being developed. The `.mcp.json` file is configured correctly, but:
- Claude Code may not support all MCP servers yet
- The Neon MCP might require additional setup
- Manual setup is actually faster anyway!

## Next Steps

Once database is set up:
1. Start backend: `python start_server.py`
2. Test at: http://localhost:8000/docs
3. Begin Phase 2!