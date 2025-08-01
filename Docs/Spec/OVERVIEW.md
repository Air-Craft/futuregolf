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

### iOS App
- **Swift/iOS** with SwiftUI and LiquidGlass styling
- **TTS** using OpenAI text-to-speech API
- **AVFoundation** for audio/video playback and recording

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


### Documentation

- Always document the development and tests in the respective files in `Docs/Dev` looking for existing relevant files first and creating any needed.


*Detailed testing procedures and scenarios are documented in Spec/Testing/*

## Project Organization

### Domain-Specific Specifications
- **Spec/Backend/** - API design, AI analysis, authentication, database models, file storage
- **Spec/Frontend/** - iOS user journey, video recording/playback, TTS integration, navigation
- **Spec/Business/** - Subscription model, monetization strategy
- **Spec/Testing/** - Detailed testing strategy, scenarios, and MCP integration

