

# SWING ANALYSIS SCREEN

Users come to the screen immediately after submitting a video for processing and also in order to view a previous previously processed video. 
Suitable placeholder should be implemented while the a video is currently processing.

## Layout

1. Video thumbnail with play button on top. Handle both orientation possibilities elegantly.
2. **Overview box** with some stats: Overall Score, Avg Head Speed, and one compliment and one critique. Icons indicating each.
3. **Analysis Section** -- A series of thumbnails at key moments with the analysis for those moments underneath
4. **Summary Box** -- An additional summary box with more analysis.

The whole page is scrollable.


### Video Processing Mode

While the video is being processed we should show a simplified verison of this screen

* Thumbnail with animated busy / processing indicator
* Slim progress bar based on feedback from server / polling
* Small text indicating status (uploading, analyzing, downloading)
* The section below (summary box, etc) is grouped and collapsed. 
* When processing and download completes, the section is populated and animated to expand


## Post-Analysis

* Analyse should return JSON
* Stills should be taken from the video at timestamps indicated in the JSON that correspond to the feedback
* These stills, and feedback constitute a block entry in the Analysis section.
* The summary text is supplied from the resultant JSON
* A sound should indicate that the analysis is complete and ready for view.
* If the user animated away from this screen there should be a toast at the bottom that with the progress bar




## Journeys

* Click on the video thumbnail, segway to Video Playback Screen
* Scrolls. Sees the content of the Analysis and Summary Box
* Click back - Goes back to Home Screen



## Additional Notes 







