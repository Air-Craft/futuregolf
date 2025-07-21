
# Overview: FutureGolf — AI Golf Swing Analyzer 

Build a cross-platform mobile app to record video of a user's golf swing and analyze it with an LLM to make suggestions for improvement. 

## Feature Summary
* Account creation required to use
* User records video of a few golf swings
* Detect shoulder angle and head alignment, etc
* AI analyzes the video and pose data and gives tips with time stamps
* Video is replayed with angle lines and tips for improvement
* Tips are spoken to the user as an LLM generated coaching script
* Angle lines change from green to red when non-optimal (if LLM can handle this)
* User can save video
* Trial version limited to 3m analyse
### Pro Feature
* Up to 1 hour (??) of total video per month. 
* Compositing of body angle lines onto final video with colour indication of when right/wrong (green/red)
* Summary Report: Scrollable page with screenshots of key moments and related tips
* Practice tips based on issues

## Main User Journey
### Onboarding
* Splash screen, animates away
* Create an account
	* Incorporating OAuth logins from Google, LinkedIn, Microsoft
### Analysis Phase I: Setup
* Straight to video recorder with TTS speaking "Let's analyze your swing" (see Custom Widget below) and then a button to begin
* Another TTS Speech that instructs the user to pick up the club and get into position
* Help user get into position: 
	* Snapshots are taken every N seconds (set via a constant. lets start with 2s) 
	* They are submitted to an LLM with prompting to determin whether the person is in frame and whether the video is likely to have a view of the full golf swing. Give positioning instructions if not (e.g. move closer, farther, left, right, etc)
	* Instructions are spoken to the user
	* Once they are in a good position play a suitable sound and say "That's perfect. Recording has begun. Begin taking swings when you are ready"

### Analysis Phase 2: Recording
* Video starts recording at hi-frame rate for a fixed 30s 
* Indicate time progress with soft beep sound at 10s, 20s and countdown beeps at 5...1
* Also indicate time with counter clock viewable at a distance
* Have a stop button on the video recorder
* Segue to processing screen showing a still from the video
* Voice tells user: We're uploading your video and waiting for it to process

### Analysis Phase 3: Analysis
* Video auto-submitted to server
* Upload and processing progress indicator
* Server analyses the video (see Phase 3 document)
* New video generated with composite of pose lines
* Video link returned along with analysis data

### Analysis Phase 4: Reporting
* When analysis and video generation is complete the user is presented with a full screen video player with usual controls and with an easy 10s back/forward and ability to enter/exit slow-motion (0.25x) with a single tap
* TTS plays the script at designated timestamps. This is regardless of the playspeed 
* Video lives in user's library. Options to export (save to photos) or deleted

## Tech Stack
* React Native frontend with Expo
* Python + Flask or FastAPI for backend (non-blocking)
* All processing handled/proxied through the server (except TTS which can be direct)
* Assembly.ai for Speech to text
* Use ElevenLabs for TTS
* Use Google Gemini to analyze the video
* MediaPipe::Pose library for body angles
* Postgres DB with JSONB field for report information for user
* Let all prompt templates live in their own files in a single folder
* Use E2D TDD to be able to take screenshots and to check your work as you go.
* Use Peekaboo to be able to see/screenshot the outcome from iOS simulator

## UI

### Style
* Sleek, sophisticated, subtle, modern, bold. Something a CEO of a big company would feel at home in
* Translucency, glass blur, dynamic animations, responsive buttons
* Use sexy female voice for flow instructions and getting into position 
* Use a relaxed but enthusiastic deep, thick male voice for the coaching script

### Custom Widgets
* Custom UI Widget for dynamic, real time visual representation of when the TTS communicates to the user:
* Custom video player with slow down button and quick jumps.

## Development Instruction
* In the folder Spec/ you will find this document Overview.md for reviewing the overview later when you need to. Make note of this in your long term memory.
* Additionally, in the Dev subfolder there are the documents for each phase of development. Begin with Phase 1 and report back when it is fully complete and all tests are written and passing
* Spawn multiple instance to work in parallel when you can. 
* Use git and feature branches to work in parallel. Commit fairly often
* Do not mention Claude Code or any reference to being AI in the commit message.