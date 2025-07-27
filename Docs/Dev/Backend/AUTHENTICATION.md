# Authentication System

## OAuth Integration

### Supported Providers
- **Google**: Primary OAuth provider for ease of use
- **Microsoft**: Corporate/enterprise users
- **LinkedIn**: Professional network integration

### OAuth Flow
1. User selects OAuth provider on registration/login screen
2. Redirect to provider's OAuth endpoint
3. User authorizes application
4. Provider returns authorization code
5. Backend exchanges code for access token
6. Retrieve user profile information
7. Create or update user account
8. Generate JWT session token

## User Registration

### Account Creation Process
1. **OAuth Registration**: Automatic account creation via OAuth providers
2. **Profile Setup**: Collect additional golf-specific information
3. **Subscription Tier**: Assign free tier by default with upgrade options
4. **Email Verification**: Optional email confirmation for direct signups

### Required User Data
- Email address (from OAuth or direct input)
- Display name
- Profile picture (optional, from OAuth provider)
- Golf experience level (beginner/intermediate/advanced)
- Subscription status (free/pro)

## Session Management

### JWT Token Structure
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "subscription_tier": "free|pro",
  "exp": 1640995200,
  "iat": 1640908800
}
```

### Token Lifecycle
- **Access Token**: 24 hour expiration
- **Refresh Token**: 30 day expiration, stored securely
- **Automatic Refresh**: Frontend handles token refresh transparently
- **Secure Storage**: Tokens stored in secure keychain/keystore

## Authorization Middleware

### Protected Endpoints
- All `/api/v1/videos/*` endpoints require authentication
- Analysis endpoints check subscription limits
- Admin endpoints require elevated permissions

### Subscription-Based Access Control
- **Free Tier**: 3 analyses per day limit
- **Pro Tier**: Unlimited analyses
- **Rate Limiting**: Per-user rate limits based on subscription tier

## Security Features

### Password Requirements (Direct Signup)
- Minimum 8 characters
- Must include uppercase, lowercase, number
- Optional special character requirement
- Password strength indicator

### Security Headers
- CORS configuration for mobile app origins
- CSRF protection for web-based admin
- Secure cookie settings
- Rate limiting on auth endpoints

### Data Protection
- User passwords hashed with bcrypt (if direct signup)
- OAuth tokens encrypted at rest
- Personal data encryption for GDPR compliance
- Secure session invalidation on logout

## Account Management

### Profile Updates
- Change display name and golf preferences
- Update notification settings
- Manage connected OAuth accounts
- View subscription and usage statistics

### Account Deletion
- Complete data removal (GDPR compliance)
- Analysis history deletion
- Video file cleanup from storage
- OAuth account disconnection