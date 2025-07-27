# Database Models

## PostgreSQL Schema Design

### Core Tables

#### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    password_hash VARCHAR(255), -- nullable for OAuth-only users
    profile_picture_url VARCHAR(500),
    golf_experience VARCHAR(20) CHECK (golf_experience IN ('beginner', 'intermediate', 'advanced')),
    subscription_tier VARCHAR(10) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro')),
    oauth_provider VARCHAR(50), -- google, microsoft, linkedin
    oauth_provider_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

#### Videos
```sql
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename VARCHAR(255),
    file_size_bytes BIGINT,
    duration_seconds DECIMAL(5,2),
    resolution VARCHAR(20), -- e.g., "1920x1080"
    fps INTEGER,
    storage_path VARCHAR(500), -- GCS path
    gcs_blob_name VARCHAR(500),
    upload_status VARCHAR(20) DEFAULT 'uploading' CHECK (upload_status IN ('uploading', 'completed', 'failed')),
    technical_metadata JSONB, -- avoid reserved word 'metadata'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP -- soft delete
);
```

#### Video Analyses
```sql
CREATE TABLE video_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    analysis_status VARCHAR(20) DEFAULT 'queued' CHECK (analysis_status IN ('queued', 'processing', 'completed', 'failed')),
    
    -- Analysis Results (JSONB for flexibility)
    swing_analysis JSONB, -- swing phases, quality scores, pose data
    coaching_script JSONB, -- timestamped coaching feedback
    alignment_data JSONB, -- frame-by-frame alignment scores
    
    -- Video Composition
    composited_video_url VARCHAR(500),
    composited_video_gcs_path VARCHAR(500),
    
    -- Processing Metadata
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    error_message TEXT,
    gemini_model_used VARCHAR(50), -- track which model version
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Subscriptions
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier VARCHAR(10) NOT NULL CHECK (tier IN ('free', 'pro')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'paused')),
    
    -- Payment Integration
    stripe_subscription_id VARCHAR(100),
    billing_cycle VARCHAR(10) CHECK (billing_cycle IN ('monthly', 'yearly')),
    
    -- Dates
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Usage Records
```sql
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES video_analyses(id) ON DELETE SET NULL,
    
    -- Usage Tracking
    action_type VARCHAR(20) NOT NULL, -- 'analysis', 'tts_generation', etc.
    resource_consumed INTEGER DEFAULT 1, -- e.g., 1 analysis credit
    
    -- Metadata
    usage_metadata JSONB, -- flexible data for different action types
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Payments
```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
    
    -- Payment Details
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(20), -- 'stripe', 'apple_pay', 'google_pay'
    
    -- External References
    stripe_payment_intent_id VARCHAR(100),
    stripe_invoice_id VARCHAR(100),
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);
```

## JSONB Field Structures

### Swing Analysis Format
```json
{
  "swing_phases": [
    {
      "phase": "setup",
      "start_frame": 0,
      "end_frame": 45,
      "duration_seconds": 1.5,
      "quality_score": 0.85,
      "key_points": ["good_posture", "proper_grip"]
    }
  ],
  "overall_score": 0.78,
  "improvement_areas": ["backswing_tempo", "follow_through"]
}
```

### Coaching Script Format
```json
{
  "script_entries": [
    {
      "timestamp": 2.5,
      "text": "Notice your excellent setup position here",
      "emphasis": "positive",
      "voice_settings": {
        "voice": "onyx",
        "speed": 1.0
      }
    }
  ],
  "total_duration": 45.2
}
```

### Technical Metadata Format
```json
{
  "encoding": "h264",
  "bitrate": 5000000,
  "color_space": "yuv420p",
  "camera_type": "front_facing",
  "device_info": {
    "model": "iPhone 14 Pro",
    "os_version": "iOS 16.4"
  }
}
```

## Indexes and Performance

### Primary Indexes
- `users(email)` - UNIQUE for login lookup
- `videos(user_id, created_at)` - User's video history
- `video_analyses(user_id, created_at)` - User's analysis history
- `video_analyses(status)` - Processing queue management
- `usage_records(user_id, recorded_at)` - Usage tracking queries

### JSONB Indexes
- `video_analyses USING GIN (swing_analysis)` - Search within analysis data
- `video_analyses USING GIN (coaching_script)` - Search coaching content

## Data Retention

### Free Tier
- Videos: 30 days retention
- Analysis results: 90 days retention

### Pro Tier  
- Videos: 1 year retention
- Analysis results: Unlimited retention

### Soft Deletes
- Videos marked with `deleted_at` timestamp
- Background cleanup process removes old soft-deleted records