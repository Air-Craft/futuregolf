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

These specifications contain the authoritative requirements and implementation details organized by functional domain.

## Project Overview

FutureGolf is an AI-powered golf swing analyzer mobile application that records golf swings, analyzes them using AI, and provides personalized coaching feedback with advanced text-to-speech capabilities.

See Spec/OVERVIEW.md for more details

## Development Approach

This project follows E2D TDD (End-to-End Test-Driven Development) methodology. All features should be developed with tests written first. See OVERVIEW.md for more details


## Current Status

* Backend functional complete more or less.

* Frontend being reworked in iOS. Some prototyping in place but final designs and flows not implemented.


