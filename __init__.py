"""			
Create coloured markers on top of Maya's native timeline. Comments can be 
added to each marker that appear as tool tips.

.. figure:: https://github.com/robertjoosten/rjTimelineMarker/raw/master/README.gif
   :align: center
   
`Link to Video <https://vimeo.com/126181906>`_

Installation
============
Copy the **rjTimelineMarker** folder to your Maya scripts directory
::
    C:/Users/<USER>/Documents/maya/scripts
    
Usage
=====
Add the interface and functionality to Maya
::
    import maya.cmds as cmds
    cmds.evalDeferred(
        "import rjTimelineMarker; rjTimelineMarker.install()"
    )
    
This line of code can also be added in the userSetup.py if you would like 
the functionality to persist.
    
Note
====
The UI elements are added to the timeline menu and can be accessed by 
right clicking on the timeline. You have the option to change the color 
of your marker points and also add comments where necessary. ToolTips 
will appear to show the comment while hovering over the timeline. 
The markers are stored in the maya file.

Hotkey
======
The hotkey function can be used to setup hotkeys to manage the timeline 
markers. There are three options, this is to either add, remove or clear 
the markers. Make sure the language is set to python.
::
    import rjTimelineMarker
    rjTimelineMarker.hotkey('add')
    rjTimelineMarker.hotkey('remove')
    rjTimelineMarker.hotkey('clear')
    
Command Line
============
The following functions can be used outside of the ui. Make sure the 
language is set to python.
::
    import rjTimelineMarker 
    rjTimelineMarker.add(frame, color, comment)
    rjTimelineMarker.remove(frames)
    rjTimelineMarker.clear()
    rjTimelineMarker.set(frames, colors, comments)
    
Code
====
"""

__author__    = "Robert Joosten"
__version__   = "0.9.9"
__email__     = "rwm.joosten@gmail.com"

from functools import wraps
from . import ui

def install():
    """
    Add the marker functionality to Maya's native timeline menu. If 
    rjTimelineMarker is already installed it will remove the previous 
    instance.
    """
    global TIMELINE_MARKER
    TIMELINE_MARKER = ui.TimelineMarker()
    
# ----------------------------------------------------------------------------

def getTimelineMarker(func):
    """
    This decorator will only run the function if the timeline marker can be 
    found, if this is not the case an error will be raised. The timeline 
    marker will be parsed as the first argument into the function provided.
    
    :raises ValueError: if timeline marker cannot be found in globals
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not "TIMELINE_MARKER" in globals().keys():
            raise ValueError("Timeline Marker not installed!")
            
        timelineMarker = globals().get("TIMELINE_MARKER")
        return func(timelineMarker, *args, **kwargs)
    return wrapper
        
# ----------------------------------------------------------------------------   
   
@getTimelineMarker
def hotkey(timelineMarker, action):
    """
    Use this function to setup hotkeys that interact with the timeline marker.
    There are 3 actions available ( "add", "remove", "clear" ).
    
    * Add - Add markers at the selected time.
    * Remove - Remove markers at the selected time.
    * Clear - Remove all markers.

    :param TimelineMarker timelineMarker: decorator handles this argument
    :param str action: Hotkey action
    """
    if action == "add":
        timelineMarker.addFromUI()
    elif action == "remove":                        
        timelineMarker.removeFromUI()
    elif action == "clear":                         
        timelineMarker.clear()

# ---------------------------------------------------------------------------- 

@getTimelineMarker
def add(timelineMarker, frame, color, comment=""):
    """
    Use this function to add markers with the provided arguments. If a marker
    already exists on the provided frame number, the old data will be 
    overwritten.

    :param TimelineMarker timelineMarker: decorator handles this argument
    :param str frame: Frame number
    :param str color: Color list [R, G, B], values between 0-255
    :param str comment: Comment
    """
    timelineMarker.add(frame, color, comment)
    
@getTimelineMarker
def remove(timelineMarker, frames):
    """
    Use this function to remove markers with the provided arguments.

    :param TimelineMarker timelineMarker: decorator handles this argument
    :param list frames: Frame numbers
    """
    if not type(frames) == list:
        frames = [frames]
    
    for frame in frames:
        timelineMarker.remove(frame)
        
@getTimelineMarker
def clear(timelineMarker):
    """
    Use this function to remove all markers.

    :param TimelineMarker timelineMarker: decorator handles this argument
    """
    timelineMarker.clear()
        
# ---------------------------------------------------------------------------- 

@getTimelineMarker
def set(timelineMarker, frames=[], colors=[], comments=[]):
    """
    Use this function to overwrite the entire marker data set with the 
    provided arguments. All existing markers will be removed.

    :param TimelineMarker timelineMarker: decorator handles this argument
    :param list frames: Frame numbers
    :param list colors: Color list [R, G, B], values between 0-255
    :param list comments: Comments
    """
    timelineMarker.clear()
    for frame, color, comment in zip(frames, colors, comments):
        timelineMarker.add(frame, color, comment)