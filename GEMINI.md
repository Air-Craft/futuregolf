# Golf Swing Analyzer AI

## Project Overview

This is a full-stack application designed to analyze golf swings using AI. It consists of an iOS frontend and a Python backend.

**Key Technologies:**

*   **Backend:** Python, FastAPI, PostgreSQL (Neon), SQLAlchemy
*   **Frontend:** Swift, SwiftUI
*   **AI/ML:** Google Gemini (video analysis), OpenAI (TTS), MediaPipe (pose detection)
*   **Storage:** Google Cloud Storage
*   **Package Management:** PDM (Python), Swift Package Manager (iOS)

**Architecture:**

The application follows a client-server architecture. The iOS app records the user's golf swing, uploads it to the backend, which then analyzes the video using a pipeline of AI/ML services. The analysis results, including coaching feedback, are then sent back to the app.

## Building and Running

### Prerequisites

*   Python 3.10
*   `pdm`
*   Xcode

### Setup

1.  **Install Dependencies:**
    ```bash
    make setup
    ```

### Running the Application

1.  **Start Backend and Frontend:**
    ```bash
    make start
    ```
    or
    ```bash
    ./start.sh
    ```

2.  **Run Backend Only:**
    ```bash
    make backend
    ```

3.  **Run iOS App:**
    Open `ios/FutureGolf/FutureGolf.xcodeproj` in Xcode and run the app on a simulator or a physical device.

### Testing

*   **Backend:** The `README.md` mentions API endpoints for health checks and other services, but does not specify a command for running tests.
*   **iOS:** No testing instructions are provided in the `README.md`.

## Development Conventions

*   The project uses `make` for task automation.
*   Python dependencies are managed with `pdm`.
*   The backend follows standard FastAPI project structure.
*   The iOS project structure is not immediately clear from the file listing.
*   The `README.md` provides detailed instructions for setting up the development environment, including handling of credentials and environment variables.
