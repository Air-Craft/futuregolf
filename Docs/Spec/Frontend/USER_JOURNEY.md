# User Journey Specification

## Complete Flow: Onboarding → Analysis → Results

### 1. Onboarding Experience

#### Splash Screen
- **Animation**: Golf swing arc animation that "swipes away" to reveal main app
- **Duration**: 2-3 seconds with smooth transition
- **Branding**: FutureGolf logo with tagline "Perfect Your Swing with AI"
- **Auto-progression**: No user interaction required

#### Account Creation
- **OAuth Priority**: Prominent Google/Microsoft/LinkedIn login buttons
- **Direct Signup**: Alternative email/password option (secondary)
- **Golf Profile**: Experience level selection (beginner/intermediate/advanced)
- **Subscription Intro**: Brief explanation of free vs pro features
- **Welcome TTS**: "Welcome to FutureGolf. Let's perfect your swing together"

### 2. Home Screen Experience

#### Main Interface
- **Primary CTA**: Large "Analyze Swing" button (record button styling)
- **Analysis History**: Scrollable list of previous recordings with thumbnails
- **Account Status**: Profile icon with subscription tier indicator
- **Usage Display**: Free tier shows "2 of 3 analyses remaining today"

#### Navigation Elements
- **Tab Bar**: Home, Analysis, Profile, Test (for development)
- **Quick Actions**: Recent analysis shortcut, help/tutorial access
- **Notifications**: Analysis completion alerts, subscription reminders

### 3. Recording Flow

#### Pre-Recording Setup
1. **Initial TTS Instruction**: "Let's analyze your swing. I'll help you get positioned perfectly"
2. **Positioning Assistant**: 
   - Snapshots every 2 seconds
   - AI analysis of user position and framing
   - Spoken guidance: "Move a step closer", "Turn slightly left", etc.
3. **Ready Confirmation**: "Perfect! Recording will begin in 3... 2... 1..."

#### Recording Interface
- **Duration**: 30 seconds default (configurable in constants)
- **Visual Indicators**: 
  - Large countdown timer visible from distance
  - Recording indicator (red dot pulsing)
  - Progress bar showing time remaining
- **Audio Cues**:
  - Soft beep at 10s and 20s marks
  - Countdown beeps at 5, 4, 3, 2, 1
  - Start/stop confirmation sounds
- **Controls**:
  - Stop button for early termination
  - Cancel option with confirmation

#### Camera Configuration
- **Frame Rate**: 60fps for smooth analysis
- **Resolution**: 1080p minimum, 4K if device supports
- **Orientation**: Portrait mode with user positioned in center frame
- **Focus**: Auto-focus with tap-to-focus option

### 4. Processing Phase

#### Upload Progress
- **Still Frame Display**: Show representative frame from recorded video
- **Progress Indicators**:
  - Upload progress (0-100%)
  - Analysis queue position
  - Processing stages: "Uploading", "Analyzing swing", "Generating feedback"
- **TTS Updates**: "We're uploading your video and analyzing your swing. This may take a minute or two"

#### Processing Stages
1. **Video Upload**: Direct to Google Cloud Storage
2. **Queue Management**: Show position in analysis queue
3. **AI Analysis**: "Analyzing swing mechanics with AI"
4. **Video Composition**: "Creating your personalized coaching video"
5. **Completion**: "Analysis complete! Let's review your swing"

### 5. Results Presentation

#### Video Player Interface
- **Full-Screen Player**: Custom video player with swing-specific controls
- **Playback Controls**:
  - Play/pause with large center button
  - Seek bar with frame-accurate scrubbing
  - 10-second back/forward jump buttons
  - Slow-motion toggle (0.25x speed) with single tap
  - Speed indicator when in slow-motion

#### Coaching Integration
- **TTS Coaching**: Automatically plays coaching script at designated timestamps
- **Visual Overlays**: 
  - Swing phase indicators ("Setup", "Backswing", "Impact", "Follow-through")
  - Body alignment lines with color coding (green=good, red=needs improvement)
  - Quality score display during relevant phases
- **Script Synchronization**: Coaching audio plays regardless of playback speed

#### Analysis Tabs
- **Video Tab**: Main playback with overlays and coaching
- **Coaching Tab**: Text-based coaching tips with TTS playback option
- **Analysis Tab**: Detailed breakdown of swing phases and scores
- **Progress Tab**: (Pro feature) Comparison with previous swings

### 6. Video Management

#### Library Features
- **Save Options**: 
  - Keep in app library
  - Export to device photo library
  - Share via social media or messaging
- **Organization**: 
  - Chronological listing with thumbnails
  - Filter by date range or quality score
  - Search by coaching notes or improvement areas
- **Deletion**: Soft delete with 30-day recovery period

### 7. Subscription Flow

#### Free Tier Limitations
- **Usage Counter**: "2 of 3 analyses remaining today" prominently displayed
- **Upgrade Prompts**: Gentle reminders on home screen and after analyses
- **Feature Previews**: Show pro features with "upgrade to unlock" messaging

#### Pro Upgrade Process
- **Benefits Overview**: Unlimited analyses, progress tracking, detailed reports
- **Pricing Options**: Monthly and annual subscriptions
- **Payment Integration**: Stripe for web, Apple Pay/Google Pay for native
- **Instant Access**: Immediate feature unlock after successful payment

### 8. Error Handling & Edge Cases

#### Network Issues
- **Upload Retry**: Automatic retry with exponential backoff
- **Offline Mode**: Queue recordings for upload when connection restored
- **Error Messages**: Clear, actionable error descriptions with retry options

#### Analysis Failures
- **AI Service Errors**: "Analysis temporarily unavailable, please try again"
- **Video Quality Issues**: "Video quality too low for accurate analysis"
- **Fallback Options**: Offer manual coaching tips when automated analysis fails

#### Device Limitations
- **Camera Permissions**: Clear instructions for enabling camera access
- **Storage Space**: Warning when device storage low
- **Performance**: Graceful degradation on older devices