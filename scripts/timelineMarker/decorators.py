from functools import wraps
from . import ui

def getTimelineMarker(func):
    """
    This decorator will only run the function if the timeline marker can be 
    found, if this is not the case an error will be raised. The timeline 
    marker will be parsed as the first argument into the function provided.
    
    :raises ValueError: if timeline marker doesn't exist
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # get timeline marker
        timelineMarker = ui.TIMELINE_MARKER
        
        # validate timeline marker
        if not timelineMarker:
            raise ValueError("Timeline Marker not installed!")
            
        # run function
        return func(timelineMarker, *args, **kwargs)
    return wrapper