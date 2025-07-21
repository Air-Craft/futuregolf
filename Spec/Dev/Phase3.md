# Development Instructions Phase 3
## Video Analysis (Server-side)
* Video uploading to the polling system
* Polling endpoint availble for frontend to check progress 
* Use MediaPipe Pose library to get the positions of shoulders, arms, head, and torso at key intervals
* Submit video to the LLM:
	* I'm not sure if we should submit stills every 30 frames / 0.1s or submit the whole video. Whatever is best for cost and speed
* Also we should aim for the lowest resolution needed to reduce bandwidth and token cost
* LLM is prompted to analyze the swings and to produce a json file with fields:
	* updates: array of... 
		* timestamp
		* type: [alignment, tip] (either or both - for alignment state changes and tips)
		* alignments: {shoulders: 1, head: 0, torso: 1, legUpperLeft: 0, ....] // 0 = bad alignment, 1 = optimal alignment
		* tip: "..."
* LLM is then give this data and prompted to make a script elaborating on the given data and produce an array of coaching text at various timestamps to be read aloud. 
	* "coachingScript": [{"timestamp": ..., "script": ""}, ...]
* This is all returned to the user along with an analyzedVideoURL
* A test video will be supplied for creating server tests.

