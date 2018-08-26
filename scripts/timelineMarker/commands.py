from . import decorators


@decorators.getTimelineMarker
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
    
    
@decorators.getTimelineMarker
def remove(timelineMarker, frames):
    """
    Use this function to remove markers with the provided arguments.

    :param TimelineMarker timelineMarker: decorator handles this argument
    :param int/list frames: Frame numbers
    """
    if not type(frames) == list:
        frames = [frames]
    
    for frame in frames:
        timelineMarker.remove(frame)
        
        
@decorators.getTimelineMarker
def clear(timelineMarker):
    """
    Use this function to remove all markers.

    :param TimelineMarker timelineMarker: decorator handles this argument
    """
    timelineMarker.clear()
        
        
# ---------------------------------------------------------------------------- 


@decorators.getTimelineMarker
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
