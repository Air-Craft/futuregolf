# FutureGolf Database Setup

This document describes the database structure and setup for the FutureGolf application.

## Database Structure

The FutureGolf application uses PostgreSQL with the following main models:

### Core Models

1. **User** - User authentication and profile management
2. **Video** - User video uploads and metadata
3. **VideoAnalysis** - AI analysis results with JSONB fields
4. **Subscription** - User subscription management
5. **Payment** - Payment tracking
6. **UsageRecord** - Usage tracking for billing

### Model Relationships

```
User (1) -----> (N) Video
User (1) -----> (N) VideoAnalysis
User (1) -----> (N) Subscription
Video (1) -----> (1) VideoAnalysis
Subscription (1) -----> (N) Payment
Subscription (1) -----> (N) UsageRecord
```

## Key Features

### JSONB Storage
- `VideoAnalysis.pose_data` - MediaPipe pose detection results
- `VideoAnalysis.ai_analysis` - AI analysis from Gemini
- `VideoAnalysis.coaching_script` - Generated coaching script with timestamps
- `VideoAnalysis.angle_lines_data` - Data for overlay lines
- `VideoAnalysis.key_moments` - Key moments for summary report

### Authentication Support
- Email/password authentication
- OAuth support (Google, Microsoft, LinkedIn)
- Email verification and password reset

### Subscription Management
- Trial accounts (3 analyses)
- Pro accounts (1 hour video per month)
- Usage tracking and billing

## Environment Variables

Set these environment variables:

```bash
DATABASE_URL=postgresql://username:password@localhost:5432/futuregolf
SQL_ECHO=false  # Set to true for SQL debugging
ENVIRONMENT=development  # Set to production in production
```

## Database Initialization

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database:
```bash
python scripts/init_db.py
```

3. Reset database (development only):
```bash
python scripts/init_db.py --reset
```

## Sample Data

In development mode, the initialization script creates:
- Admin user: `admin@futuregolf.com`
- Trial user: `trial@futuregolf.com`
- Sample subscription for admin user

## Database Indexes

The system creates performance indexes for:
- User email lookups
- Video queries by user and status
- Video analysis queries
- Subscription lookups
- Usage record queries by billing period

## Migration Management

Use Alembic for database migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```