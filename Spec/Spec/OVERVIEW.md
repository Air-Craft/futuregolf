# FutureGolf — AI Golf Swing Analyzer

AI-powered mobile app that records golf swings, analyzes them using AI, and provides personalized coaching feedback with advanced text-to-speech capabilities.

## Core Features
- **Video Recording**: High-frame rate golf swing capture with positioning assistance
- **AI Analysis**: Google Gemini video analysis with MediaPipe pose detection
- **Coaching Feedback**: TTS voice overtop of slow motion video playback
- **Record of Analyses**: Playback and analysis history
- **Visual Overlays**: Swing path and body position indicators with color-coded alignment
- **User Management**: OAuth authentication with free/pro subscription tiers

## Tech Stack

### Frontend
- **iOS/Swift** with SwiftUI and LiquidGlass styling
- **TTS** using OpenAI Whisper fast text-to-speech


### Former front-end stack 
(which we might resurrect at some point but ignore for now)
- **React Native** with Expo for cross-platform mobile development
- **Expo AV** for audio playback and analysis

### Backend
- **Python** with FastAPI (production-ready)
- **PostgreSQL** with JSONB fields for storing analysis reports
- **OpenAI API** for high-quality Text-to-Speech
- **Google Gemini** for video analysis
- **MediaPipe::Pose** for body angle detection

### Infrastructure
- **Neon** for PostgreSQL database hosting
- **Google Cloud Storage** for video files (bucket: `fg-video`)

## Development Strategy

### Methodology
- **E2D TDD** (End-to-End Test-Driven Development) - all features developed with tests written first
- **Parallel development** - multiple feature branches with frequent commits
- **Git workflow** - feature branches, regular commits, no AI references in commit messages

### Testing Approach
- **Screenshot testing** with iOS simulator via MCP integration
- **Unit tests** for components with comprehensive mocking
- **Integration tests** for complete pipeline validation
- **E2E tests** from video upload to analysis output

*Detailed testing procedures and scenarios are documented in Spec/Testing/*

## Project Organization

### Domain-Specific Specifications
- **Spec/Backend/** - API design, AI analysis, authentication, database models, file storage
- **Spec/Frontend/** - User journey, video recording/playback, TTS integration, navigation
- **Spec/Business/** - Subscription model, monetization strategy
- **Spec/Testing/** - Detailed testing strategy, scenarios, and MCP integration

