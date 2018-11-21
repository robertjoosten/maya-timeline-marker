import maya.cmds as cmds

if not cmds.about(batch=True):
    import timelineMarker
    cmds.evalDeferred(timelineMarker.install)
