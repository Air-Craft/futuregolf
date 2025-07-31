# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPORTANT: Always Check Specifications First

When lacking context about what to do next or how to implement features, ALWAYS check the specification documents in this order:

1. **`Spec/OVERVIEW.md`** - Core project vision, tech stack, and development strategy
2. **Domain-specific specifications** based on your work area:
   - **Backend work**: Check `Spec/Backend/` for API design, AI analysis, auth, database, storage
   - **Frontend work**: Check `Spec/Frontend/` for user journey, video recording/playback, TTS, navigation
   - **Business logic**: Check `Spec/Business/` for subscription model and monetization
   - **Testing**: Check `Spec/Testing/` for testing strategy and scenarios
3. Always follow the development guidelines in `Docs/Spec/DEVELOPMENT_GUIDELINES.md`. If guidance is not explicit in this document, follow industry best practices, researching those online if need be first. 


These specifications contain the authoritative requirements and implementation details organized by functional domain.

## Development Documentation

For implementation details and troubleshooting, check the development docs:

### Frontend Development
- **`Docs/Dev/Frontend/ON_DEVICE_STT.md`** - On-device speech recognition implementation
- **`Docs/Dev/Frontend/TTS_SERVICE.md`** - Text-to-speech service configuration
- **`Docs/Dev/Frontend/CAMERA_CONFIGURATION.md`** - Camera setup and frame rate optimization

### Backend Development
- **`Docs/Dev/Backend/`** - API design, authentication, database models, storage

### Troubleshooting
- **`Docs/Dev/TROUBLESHOOTING.md`** - Common issues and solutions, debug features
- **`Docs/Dev/DEBUG_FEATURES.md`** - Debug tools and environment variables

### DevOps
- **`Docs/Dev/DEVOPS.md`** - Deployment and infrastructure

## Project Overview

FutureGolf is an AI-powered golf swing analyzer mobile application that records golf swings, analyzes them using AI, and provides personalized coaching feedback with advanced text-to-speech capabilities.

See Spec/OVERVIEW.md for more details

## Development Approach

### Components

#### Frontend
Swift/iOS (latest)

#### Backend
Python v3.10

IMPORTANT: For backend be sure to source `source .venv/bin/activate`. If the venv does not exist then create it based on python 3.10.x. Install it with pyenv if 3.10 is not available.


### Methodology

This project follows E2D TDD (End-to-End Test-Driven Development) methodology. All features should be developed with tests written first. See OVERVIEW.md for more details



## Current Status

* Backend functional complete more or less.

* Frontend being reworked in iOS. Some prototyping in place but final designs and flows not implemented.


