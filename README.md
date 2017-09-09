# rjTimelineMarker
Create coloured markers on top of Maya's native timeline. Comments can be added to each marker that appear as tool tips.

<p align="center"><img src="https://github.com/robertjoosten/rjTimelineMarker/blob/master/README.gif"></p>
<a href="https://vimeo.com/126181906" target="_blank"><p align="center">Click for video</p></a>

## Installation
Copy the **rjTimelineMarker** folder to your Maya scripts directory:
> C:\Users\<USER>\Documents\maya\scripts

## Usage
Add the interface and functionality to Maya:
```python
import maya.cmds as cmds
cmds.evalDeferred("import rjTimelineMarker; rjTimelineMarker.install()")
```
This line of code can also be added in the userSetup.py if you would like the functionality to persist.

## Note
The UI elements are added to the timeline menu and can be accessed by right clicking on the timeline. You have the option to change the color of your marker points and also add comments where necessary. ToolTips will appear to show the comment while hovering over the timeline. The markers are stored in the maya file.

## Hotkey
The hotkey function can be used to setup hotkeys to manage the timeline markers. There are three options, this is to either add, remove or clear the markers. Make sure the language is set to python.

```python
import rjTimelineMarker; rjTimelineMarker.hotkey("add")
import rjTimelineMarker; rjTimelineMarker.hotkey("remove")
import rjTimelineMarker; rjTimelineMarker.hotkey("clear")
```

## Command line
The following functions can be used outside of the ui. Make sure the 
language is set to python.

```python
import rjTimelineMarker; rjTimelineMarker.add(frame, color, comment)
import rjTimelineMarker; rjTimelineMarker.remove(frames)
import rjTimelineMarker; rjTimelineMarker.clear()
import rjTimelineMarker; rjTimelineMarker.set(frames, colors, comments)
```    
