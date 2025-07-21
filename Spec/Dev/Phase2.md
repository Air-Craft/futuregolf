# Development Instructions Phase 2
## Core UI Components
* Create the TTS service (frontend) 
* Create the TTS popup widget (see below)
* Create a splash screen that animates away like a golf swing arc
* Create the intro screen
* Create the user registration flow
* Home screen is...
	* Big "Analyze Swing" button that looks a bit like a record button too
	* A table of previous recordings
	* An account icon up top
* Create the video record screen and the initial TTS Popup instruction
* Create the video playback screen with its various controls
	* play/pause
	* seek
	* back/forward 10s
	* Slow-mo toggle
* Let the app begin the recording as specified in the Overview's "Main User Journey" section
	* Have the record length be set in a global constants file
* When the recording is finished, go to a player and have just the recorded video play (no processing yet) to test the UI

### TTS Popup Widget
When the TTS voice speaks have a pop up come up. 
* It has an animated circular pulsing widget that is synchronised to the RMS of the talking waveform. 
* It is translucent/blurred and looks good over video or any arbitrary background
* It shows the words below in chunks to fit into the space
* It can cross fade into a prompt with a message and a button, e.g. "Let's get started" \[Analyze my swing\]

