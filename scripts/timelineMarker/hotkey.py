from . import decorators


@decorators.getTimelineMarker
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
