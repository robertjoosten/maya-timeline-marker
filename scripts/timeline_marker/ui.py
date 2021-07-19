import json
from maya import mel
from maya import cmds
from maya.api import OpenMaya
from collections import defaultdict
from PySide2 import QtWidgets, QtGui, QtCore

from timeline_marker import utils


TIMELINE_MARKER = "timeline-marker"
TIMELINE_MARKER_OLD = "timelineMarker"


class TimelineMark(object):
    slots = ("colour", "comment", )

    def __init__(self, colour=None, comment=None):
        self.colour = colour
        self.comment = comment


class TimelineMarkerManager(object):
    """
    This manager is required as in certain version of PySide2 the __new__
    method is not allowed to be subclasses which makes it not possible to
    create a singleton.
    """
    instance = None

    @classmethod
    def create(cls, parent):
        if cls.instance is None:
            cls.instance = TimelineMarker(parent)

        return cls.instance

    @classmethod
    def get_instance(cls):
        """
        :return: Timeline marker instance
        :rtype: TimelineMarker
        """
        if cls.instance is None:
            raise RuntimeError("TimelineMarker has no instance, initialize first.")

        return cls.instance


class TimelineMarker(QtWidgets.QWidget):
    def __init__(self, parent):
        super(TimelineMarker, self).__init__(parent)

        # variables
        self.start = None
        self.end = None
        self.total = None
        self.step = None

        self.data = defaultdict(TimelineMark)
        self.range = None
        self.callbacks = []

        # set menu
        scale_factor = self.logicalDpiX() / 96.0
        self.menu = utils.get_timeline_menu()
        self.menu_actions = []
        self.menu_actions.append(self.menu.addSeparator())

        # create marker comment field
        self.comment = QtWidgets.QLineEdit(self.menu)
        self.comment.setPlaceholderText("marker comment...")

        action = QtWidgets.QWidgetAction(self.menu)
        action.setDefaultWidget(self.comment)
        self.menu.addAction(action)
        self.menu_actions.append(action)
        self.menu_actions.append(self.menu.addSeparator())

        # create marker colour picker
        self.picker = self.menu.addAction("Pick Color")
        self.picker.setProperty("rgb", [0, 255, 0])
        self.picker.triggered.connect(self.display_picker)

        pixmap = QtGui.QPixmap(12 * scale_factor, 12 * scale_factor)
        pixmap.fill(QtGui.QColor(0, 255, 0))
        self.picker.setIcon(QtGui.QIcon(pixmap))
        self.menu_actions.append(self.picker)
        self.menu_actions.append(self.menu.addSeparator())

        # create marker actions
        add_action = self.menu.addAction("Add Marker")
        add_action.triggered.connect(self.add_from_ui)
        remove_action = self.menu.addAction("Delete Selected Marker")
        remove_action.triggered.connect(self.remove_from_ui)
        clear_action = self.menu.addAction("Delete All Markers")
        clear_action.triggered.connect(self.clear)
        self.menu_actions.extend([add_action, remove_action, clear_action])
        self.menu_actions.append(self.menu.addSeparator())

        self.move = self.menu.addAction("Move With Time Control")
        self.move.setCheckable(True)
        self.move.setChecked(False)
        self.menu_actions.append(self.move)

        # initialize
        self.load_from_scene()
        self.register_callbacks()

    # ------------------------------------------------------------------------

    def paintEvent(self, event):
        """
        When the paint event is called draw all of the timeline markes onto
        the widget.

        :param QtCore.QEvent event:
        :return: Event state
        :rtype: bool
        """
        # get animation range
        self.start = cmds.playbackOptions(query=True, minTime=True)
        self.end = cmds.playbackOptions(query=True, maxTime=True)

        # calculate frame width
        self.total = self.width()
        self.step = (self.total - (self.total * 0.01)) / (self.end - self.start + 1)

        # validate marker information
        if not self.data:
            return

        # setup painter and pen
        painter = QtGui.QPainter(self)
        pen = QtGui.QPen()
        pen.setWidth(self.step)

        # draw lines for each frame
        for frame, frame_data in self.data.items():
            r, g, b = frame_data.colour
            pen.setColor(QtGui.QColor(r, g, b, 50))

            pos = (frame - self.start + 0.5) * self.step + (self.total * 0.005)
            line = QtCore.QLineF(QtCore.QPointF(pos, 0), QtCore.QPointF(pos, 100))

            painter.setPen(pen)
            painter.drawLine(line)

        return super(TimelineMarker, self).paintEvent(event)

    def event(self, event):
        """
        Subclass the event function in order to capture the ToolTip event.
        The hovered frame is calculated and checked to see if it is marked
        and commented, if so the tool tip will show.

        :param QtCore.QEvent event:
        :return: Event state
        :rtype: bool
        """
        if event.type() == QtCore.QEvent.ToolTip:
            QtWidgets.QToolTip.hideText()

            frame = int(((event.x() - (self.total * 0.005)) / self.step) + self.start)
            QtWidgets.QToolTip.showText(event.globalPos(), self.data[frame].comment, self)

        return super(TimelineMarker, self).event(event)

    # ------------------------------------------------------------------------

    def update(self):
        """
        Subclass update to simultaneously store all of the marker data into
        the current scene.
        """
        self.write_to_scene()
        super(TimelineMarker, self).update()
        
    def deleteLater(self):
        """
        Subclass the deleteLater function to first remove the callback, 
        this callback shouldn't be floating around and should be deleted
        with the widget.
        """
        for action in self.menu_actions:
            action.deleteLater()

        self.remove_callbacks()
        super(TimelineMarker, self).deleteLater()

    # ------------------------------------------------------------------------

    def display_picker(self):
        """
        The picker will change the color of the button and will store the
        rgb values in a property, this property will be read when a marker is
        added via the menu.
        """
        colour = self.picker.property("rgb")
        colour = QtGui.QColor(colour[0], colour[1], colour[2])

        dialog = QtWidgets.QColorDialog.getColor(colour, self.menu)
        if not dialog.isValid():
            return

        colour = [dialog.red(), dialog.green(), dialog.blue()]
        pixmap = QtGui.QPixmap(12, 12)
        pixmap.fill(QtGui.QColor(colour[0], colour[1], colour[2]))

        self.picker.setProperty("rgb", colour)
        self.picker.setIcon(QtGui.QIcon(pixmap))

    # ------------------------------------------------------------------------

    def press_command_callback(self, *args):
        """
        Press callback on the timeline, this callback registers the current
        selected frames, if the user settings determine that the frame range
        is not important ( no automated shifting of markers ), no range will
        be stored.
        """
        timeline_path = utils.get_timeline_path()
        cmds.timeControl(timeline_path, edit=True, beginScrub=True)

        # check if range needs to be stored
        range_visible = cmds.timeControl(timeline_path, query=True, rangeVisible=True)
        if range_visible and self.move.isChecked():
            self.range = utils.get_timeline_range()
        else:
            self.range = None

    def release_command_callback(self, *args):
        """
        Release callback on the timeline, together with the press command the
        difference can be extracted and the markers can be moved accordingly.
        Theuser settings will be checked if the moving of markers is
        appropriate.
        """
        timeline_path = utils.get_timeline_path()
        cmds.timeControl(timeline_path, edit=True, endScrub=True)

        # check if markers need to be shifted
        if not self.range or not self.move.isChecked():
            return

        # get begin and end range
        start_range = self.range[:]
        end_range = utils.get_timeline_range()

        # reset stored range
        self.range = None

        # check data
        start_length = len(start_range)
        end_length = len(end_range)
        range_visible = cmds.timeControl(timeline_path, query=True, rangeVisible=True)
        if (start_length == 1 and end_length != 1) or not range_visible:
            return

        # remap frames
        matches = {frame: self.data[frame] for frame in start_range if frame in self.data}
        for frame, frame_data in matches.items():
            if start_length == 1:
                frame_remapped = end_range[0]
            else:
                frame_remapped = int(
                    utils.remap(
                        frame,
                        input_min=start_range[0],
                        input_max=start_range[-1],
                        output_min=end_range[0],
                        output_max=end_range[-1]
                    )
                )

            # continue if frame is the same
            if frame == frame_remapped:
                continue

            # update data
            self.data[frame_remapped] = frame_data
            self.data.pop(frame, None)

        self.update()

    # ------------------------------------------------------------------------

    @classmethod
    def add(cls, frame, colour, comment):
        """
        Add a marker based on the provided arguanments. If the frames are
        already marked this information will be overwritten.

        :param int frame:
        :param list[int] colour:
        :param str comment:
        """
        instance = TimelineMarkerManager.get_instance()
        instance.data[frame] = TimelineMark(colour, comment)
        instance.update()

    @classmethod
    def set(cls, frames, colours, comments):
        """
        :param list frames:
        :param list colours:
        :param list comments:
        """
        instance = TimelineMarkerManager.get_instance()
        instance.data.clear()
        for frame, colour, comment in zip(frames, colours, comments):
            instance.data[frame] = TimelineMark(colour, comment)
        instance.update()

    @classmethod
    def remove(cls, *frames):
        """
        :param int frames: Frame number
        """
        instance = TimelineMarkerManager.get_instance()
        for frame in frames:
            instance.data.pop(frame, None)
        instance.update()

    @classmethod
    def clear(cls):
        """
        Remove all markers.
        """
        instance = TimelineMarkerManager.get_instance()
        instance.data.clear()
        instance.update()

    # ------------------------------------------------------------------------

    def add_from_ui(self):
        """
        Get the frame, color and comments arguments from the UI and add
        marker(s).
        """
        # get info from menu
        colour = self.picker.property("rgb")
        comment = self.comment.text()

        # get selected frames
        for frame in utils.get_timeline_range():
            self.add(frame, colour, comment)

        # reset menu
        self.comment.setText("")

    def remove_from_ui(self):
        """
        Get the frame, color and comments arguments from the UI and remove
        marker(s).
        """
        for frame in utils.get_timeline_range():
            self.remove(frame)

    # ------------------------------------------------------------------------

    def register_callbacks(self):
        """
        Register a callback to run the read function every time a new scene is
        initialized or opened.
        """
        self.callbacks = [
            OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterNew, self.load_from_scene),
            OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterOpen, self.load_from_scene)
        ]

        timeline_path = utils.get_timeline_path()
        cmds.timeControl(
            timeline_path,
            edit=True,
            pressCommand=self.press_command_callback,
            releaseCommand=self.release_command_callback,
        )

    def remove_callbacks(self):
        """
        Remove the callbacks that update the time line markers every time a
        new scene is initialized or opened.
        """
        if self.callbacks:
            OpenMaya.MMessage.removeCallbacks(self.callbacks)

        timeline_path = utils.get_timeline_path()
        cmds.timeControl(timeline_path, edit=True, pressCommand=None, releaseCommand=None)

    # ------------------------------------------------------------------------

    def load_from_scene(self, *args):
        """
        Marker data can be stored in the Maya's scenes themselves, the
        fileInfo command is used for this and the data is stored under the
        "timeline-marker" argument. This data can be decoded with json and
        split it the frames, colours and comments, as the format has changed
        slightly loading is made backwards compatible with older versions of
        the tool.
        """
        # clear existing data
        self.data.clear()

        # get data
        data = cmds.fileInfo(TIMELINE_MARKER, query=True)
        data = json.loads(data[0].replace('\\"', '"')) if data else {}

        if not data:
            # support backwards compatibility with old method of saving.
            # once initialized using the new key, the old will always be
            # ignored.
            data = cmds.fileInfo(TIMELINE_MARKER_OLD, query=True)
            data = json.loads(data[0].replace('\\"', '"')) if data else {}
            data = {
                frame: {"colour": colour, "comment": comment}
                for frame, colour, comment in zip(
                    data.get("frames", []),
                    data.get("colors", []),
                    data.get("comments", [])
                )
            }

        for frame, frame_data in data.items():
            self.data[int(frame)] = TimelineMark(**frame_data)

        self.update()

    def write_to_scene(self):
        """
        Get all the marker information ( frames, comments and colors ) and
        store this with the fileInfo command in the maya file. Data is
        stored under the "timelineMarker" argument.
        """
        encoded = json.dumps({frame: frame_data.__dict__ for frame, frame_data in self.data.items()})
        cmds.fileInfo(TIMELINE_MARKER, encoded)
