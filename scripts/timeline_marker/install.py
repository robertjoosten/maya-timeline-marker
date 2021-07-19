import logging
from maya import mel
from PySide2 import QtWidgets, QtGui

from timeline_marker.ui import TimelineMarkerManager
from timeline_marker import utils


log = logging.getLogger(__name__)


def execute():
    """
    Add the timeline marker functionality to Maya's native timeline and
    extend its native menu with actions to manipulate the timeline
    markers.

    :raises RuntimeError: When the timeline marker is already installed.
    """
    # validate timeline marker
    if TimelineMarkerManager.instance is not None:
        raise RuntimeError("timeline-marker has already been installed.")

    # get parent
    parent = utils.get_timeline()
    layout = parent.layout()

    # create layout if non exists
    if layout is None:
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        parent.setLayout(layout)

    # create timeline marker
    timeline_marker = TimelineMarkerManager.create(parent)
    layout.addWidget(timeline_marker)

    log.info("timeline-marker installed successfully.")
