# rjTimelineMarker
Create coloured markers on top of Maya's native timeline. Comments can be added to each marker that appear as tool tips.

<p align="center"><img src="docs/_images/timelineMarkerExample.gif?raw=true"></p>
<a href="https://vimeo.com/126181906" target="_blank"><p align="center">Click for video</p></a>

## Installation
* Extract the content of the .rar file anywhere on disk.
* Drag the timelineMarker.mel file in Maya to permanently install the script.

## Note
The UI elements are added to the timeline menu and can be accessed by right clicking on the timeline. You have the option to change the color of your marker points and also add comments where necessary. ToolTips will appear to show the comment while hovering over the timeline. The markers are stored in the maya file.

## Hotkey
The hotkey function can be used to setup hotkeys to manage the timeline markers. There are three options, this is to either add, remove or clear the markers. Make sure the language is set to python.

```python
import timelineMarker; timelineMarker.hotkey("add")
import timelineMarker; timelineMarker.hotkey("remove")
import timelineMarker; timelineMarker.hotkey("clear")
```

## Command line
The following functions can be used outside of the ui. Make sure the 
language is set to python.

```python
import timelineMarker; timelineMarker.add(frame, color, comment)
import timelineMarker; timelineMarker.remove(frames)
import timelineMarker; timelineMarker.clear()
import timelineMarker; timelineMarker.set(frames, colors, comments)
```    
