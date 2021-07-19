"""			
Create coloured markers on top of Maya's native timeline. Comments can be 
added to each marker that appear as tool tips.

.. figure:: /_images/timeline-marker-example.gif
   :align: center
   
`Link to Video <https://vimeo.com/126181906>`_

Installation
============
* Extract the content of the .rar file anywhere on disk.
* Drag the timeline-marker.mel file in Maya to permanently install the script.
    
Note
====
The UI elements are added to the timeline menu and can be accessed by 
right clicking on the timeline. You have the option to change the color 
of your marker points and also add comments where necessary. ToolTips 
will appear to show the comment while hovering over the timeline. 
The markers are stored in the maya file.

Command Line + Hotkey
=====================
The following functions can be used outside of the ui and set as a hotkey.
Make sure the language is set to python.
::
    from timeline_marker.ui import TimelineMarker
    TimelineMarker.add(frame, colour, comment)
    TimelineMarker.set(frames, colours, comments)
    TimelineMarker.remove(frame)
    TimelineMarker.clear()
    
"""
__author__    = "Robert Joosten"
__version__   = "3.0.1"
__email__     = "rwm.joosten@gmail.com"
