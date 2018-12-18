import json
from maya import OpenMaya, OpenMayaUI, cmds, mel
from . import utils


# ----------------------------------------------------------------------------


global TIMELINE_MARKER
TIMELINE_MARKER = None


# ----------------------------------------------------------------------------
    
    
class TimelineMarker(utils.QWidget):
    def __init__(self):
        # get parent
        utils.QWidget.__init__(self)
        
        # variables
        self.setObjectName("timelineMarker") 
        
        # variables
        self.start = None
        self.end   = None
        self.total = None
        self.step  = None
        
        self.frames = []
        self.colors = []
        self.comments = []
        
        self.newID = None
        self.openID = None

        self._range = None

        # set menu
        self.menu = TimelineMarkerMenu(self)

        # initialize
        self.readFromCurrentScene()
        self.addCallbacks()

    # ------------------------------------------------------------------------
        
    def readFromCurrentScene(self, *args):
        """
        Marker data can be stored in the Maya's scenes themselves, the 
        fileInfo command is used for this and the data is stored under the 
        "timelineMarker" argument. This data can be decoded with json and 
        split it the frames, colours and comments.
        """
        # variable
        data = {}
        
        # read from file
        stored = cmds.fileInfo("timelineMarkers", query=True)

        if stored:      
            data = json.loads(stored[0].replace('\\"', '"'))
        
        # extract data 
        self.frames = data.get( "frames" ) or []
        self.colors = data.get( "colors" ) or [] 
        self.comments = data.get( "comments" ) or []

        # update ui
        self.update()
        
    def saveToCurrentScene(self):
        """
        Get all the marker information ( frames, comments and colors ) and 
        store this with the fileInfo command in the maya file. Data is 
        stored under the "timelineMarker" argument.
        """
        # encode data
        data = {
            "frames":self.frames,
            "colors":self.colors,
            "comments":self.comments,
        }
        encoded = json.dumps(data)
        
        # store data
        cmds.fileInfo("timelineMarkers", encoded)
        
    # ------------------------------------------------------------------------
    
    def getDataFromFrame(self, frame):
        """
        Get data from frame, this includes the index within the lists, the
        color and comment.
        
        :param int frame: Frame to get data from
        :return: index, frame, color, comment
        :rtype: tuple
        """
        if frame in self.frames:
            index = self.frames.index(frame)
            color = self.colors[index]
            comment = self.comments[index]
            
            return index, frame, color, comment
        return -1, frame, None, None
        
    # ------------------------------------------------------------------------
        
    def paintEvent(self, event):
        self.draw()
        
    def event(self, event):
        """
        Subclass the event function in order to capture the ToolTip event. 
        The hovered frame is calculated and checked to see if it is marked 
        and commented, if so the toolTip will show.
        """
        if event.type() == utils.QEvent.ToolTip:
            utils.QToolTip.hideText() 
            
            # find frame at mouse pointer
            frame = int(((event.x()-(self.total*0.005))/self.step)+self.start)
            
            # get comment for frame
            _, _, _, comment = self.getDataFromFrame(frame)
            
            # show tooltip
            utils.QToolTip.showText(event.globalPos(), comment, self)
            
        return utils.QWidget.event(self, event)
        
    # ------------------------------------------------------------------------
        
    def addFromUI(self):
        """
        Get the frame, color and comments arguments from the UI and add
        marker(s).
        """
        # get info from menu
        color = self.menu.colorA.property("rgb")
        comment = self.menu.commentL.text()
        
        # get selected frames
        for f in utils.getTimelineRange():
            self.add(f, color, comment)

        # reset menu
        self.menu.commentL.setText("")

    def add(self, frame, color, comment):
        """
        Add a marker based on the provided arguments. If the frames are 
        already marked this information will be overwritten.
        
        :param int frame: Frame number
        :param list color: Color list ( RGB )
        :param str comment: Tooltip comment
        """
        index, _, _, _ = self.getDataFromFrame(frame)
        
        # add new marker
        if index == -1:
            self.frames.append(frame)
            self.colors.append(color)
            self.comments.append(comment)
            
        # overwrite existing marker
        else:
            self.colors[index] = color
            self.comments[index] = comment

        self.update()

    # ------------------------------------------------------------------------
        
    def removeFromUI(self):
        """
        Get the frame, color and comments arguments from the UI and remove
        marker(s).
        """
        for f in utils.getTimelineRange():
            self.remove(f)

    def remove(self, frame):
        """
        Remove a marker based on the provided arguments.
        
        :param int frame: Frame number
        """
        # check if frame exists
        index, _, _, _ = self.getDataFromFrame(frame)
        if index == -1:
            return
            
        # remove data
        self.frames.pop(index)
        self.colors.pop(index)
        self.comments.pop(index)
        
        self.update()
        
    # ------------------------------------------------------------------------
        
    def clear(self):
        """
        Remove all markers.
        """
        self.frames = []
        self.colors = []
        self.comments = []

        self.update()

    # ------------------------------------------------------------------------

    def pressCommand(self, *args):
        """
        Press callback on the timeline, this callback registers the current
        selected frames, if the user settings determine that the frame range
        is not important ( no automated shifting of markers ), no range will 
        be stored.
        """
        # variable
        timeline = utils.getMayaTimeline()

        # restore sound scrub
        cmds.timeControl(timeline, edit=True, beginScrub=True)

        # get visible range
        rangeVisible = cmds.timeControl(
            timeline,
            q=True, 
            rangeVisible=True
        )
        
        # check if range needs to be stored
        if not rangeVisible or not self.menu.moveA.isChecked():
            return

        # save range
        self._range = utils.getTimelineRange()

    def releaseCommand(self, *args):
        """
        Release callback on the timeline, together with the press command the
        difference can be extracted and the markers can be moved accordingly. 
        Theuser settings will be checked if the moving of markers is 
        appropriate.
        """
        # variable
        timeline = utils.getMayaTimeline()

        # restore sound scrub
        cmds.timeControl(timeline, edit=True, endScrub=True)

        # check if markers need to be shifted
        if not self._range or not self.menu.moveA.isChecked():
            return

        # get begin and end range
        beginRange = self._range[:]
        endRange = utils.getTimelineRange()

        # reset stored range
        self._range = None

        # check data
        beginLength = len(beginRange)
        endLenght = len(endRange)
        
        rangeVisible = cmds.timeControl(
            timeline,
            q=True, 
            rangeVisible=True
        )

        if (beginLength == 1 and endLenght != 1) or not rangeVisible:
            return

        # find frames
        matchingFrames = [
            frame for frame in beginRange 
            if frame in self.frames
        ]

        # remap frames
        for frame in matchingFrames:
            if beginLength == 1:
                remappedFrame = endRange[0]
            else:
                remappedFrame = utils.remap(
                    frame,
                    beginRange[0], 
                    beginRange[-1], 
                    endRange[0],
                    endRange[-1]
                )

            # continue if frame is the same
            if frame == remappedFrame:
                continue

            # remove existing data on new frame number
            self.remove(remappedFrame)

            # update frame number
            index = self.frames.index(frame)
            self.frames[index] = remappedFrame

        self.update()

    # ------------------------------------------------------------------------

    def draw(self):
        """
        Take all the marker information and fill in the utils.QWidget covering the 
        timeline. This function will be called by the update and paintEvent 
        function.
        """
        
        # get animation range
        self.start = cmds.playbackOptions(query=True, min=True)
        self.end   = cmds.playbackOptions(query=True, max=True)
        
        # calculate frame width
        self.total = self.width()
        self.step = (self.total - (self.total*0.01)) / (self.end-self.start+1)

        # validate marker information
        if not self.frames or not self.colors: 
            return
        
        # setup painter and pen
        painter = utils.QPainter(self)
        pen = utils.QPen()
        pen.setWidth(self.step)
            
        # draw Lines for each frame
        for f, c in zip(self.frames, self.colors):
            pen.setColor(utils.QColor(c[0], c[1], c[2], 50))
        
            # calculate line position
            pos = (f-self.start+0.5) * self.step + (self.total*0.005)
            line = utils.QLineF(utils.QPointF(pos, 0), utils.QPointF(pos, 100))
            
            painter.setPen( pen )
            painter.drawLine( line )
            
    # ------------------------------------------------------------------------
            
    def addCallbacks(self):
        """
        Add callbacks that will clear all marker information on the timeline 
        every time a new file is created or a file is opened. It also adds 
        callback to determine if the markers are sliding.
        """
        # after new scene
        self.newID = OpenMaya.MSceneMessage.addCallback(
            OpenMaya.MSceneMessage.kAfterNew, 
            self.readFromCurrentScene
        )
        
        # after open scene
        self.openID = OpenMaya.MSceneMessage.addCallback(
            OpenMaya.MSceneMessage.kAfterOpen, 
            self.readFromCurrentScene
        )

        # timeline press callbacks
        cmds.timeControl(
            utils.getMayaTimeline(), 
            edit=True, 
            pressCommand=self.pressCommand,
            releaseCommand=self.releaseCommand,
        )
        
    def removeCallbacks(self):
        """
        Remove Callbacks.
        """
        # remove api callbacks
        for id_ in [self.newID, self.openID]:
            if not id_:
                continue
                
            OpenMaya.MMessage.removeCallback(id_)

        # remove timeline callbacks
        cmds.timeControl(
            utils.getMayaTimeline(), 
            edit=True, 
            pressCommand="", 
            releaseCommand=""
        )
        
    # ------------------------------------------------------------------------
    
    def update(self):
        """
        Subclass update to simultaneously store all of the marker data into
        the current scene.
        """
        self.saveToCurrentScene()
        utils.QWidget.update(self)
        
    def deleteLater(self):
        """
        Subclass the deleteLater function to first remove the callback, 
        this callback shouldn't be floating around and should be deleted
        with the widget.
        """
        self.removeCallbacks()
        utils.QWidget.deleteLater(self)

        
class TimelineMarkerMenu(object):
    def __init__(self, parent):    
        # variable
        self.menu = utils.getTimelineMenu()
        self._buttons = []
        
        # separator
        self.separatorA1 = self.addSeparator()
        
        # comment field
        pText = "marker comment"
        self.commentA, self.commentL = self.addCommentField(pText)

        # color picker
        self.colorA = self.addColorPicker()

        # separator
        self.separatorA2 = self.addSeparator()    

        # add, remove, clear markers
        aText = "Add Marker"
        rText = "Delete Selected Marker"
        cText = "Delete All Markers"
        
        self.addA = self.addButton(aText, parent.addFromUI)
        self.removeA = self.addButton(rText, parent.removeFromUI)
        self.clearA = self.addButton(cText, parent.clear)

        # separator
        self.separatorA3 = self.addSeparator()

        # move markers
        self.moveA = self.addButton(
            "Move With Time Control", 
        )
        self.moveA.setCheckable(True)
        self.moveA.setChecked(False)
        
    # ------------------------------------------------------------------------
    
    @property
    def buttons(self):
        """
        List all marker related QActions from the timeline menu.
        
        :return: Buttons
        :rtype: list
        """
        return self._buttons
        
    # ------------------------------------------------------------------------
    
    def addCommentField(self, placeholderText):
        """
        Add comment field QAction to the menu.
        
        :param str placeholderText: Placeholder text
        :return: QAction, QLineEdit
        :rtype: tuple
        """
        edit = utils.QLineEdit(self.menu)
        edit.setPlaceholderText(placeholderText)
        
        button = utils.QWidgetAction(self.menu)
        button.setDefaultWidget(edit)
        
        self.menu.addAction(button)
        self.buttons.append(button) 
        return button, edit
        
    def addColorPicker(self):
        """
        Add color picker QAction to the menu.
        
        :return: Color picker
        :rtype: QAction
        """
        button = self.addButton("Pick Color", self.picker)
        button.setProperty("rgb", [0, 255, 0])
        
        pixmap = utils.QPixmap(12, 12)
        pixmap.fill(utils.QColor(0, 255, 0))
        
        button.setIcon(utils.QIcon(pixmap))
        return button
        
    # ------------------------------------------------------------------------
    
    def addSeparator(self):
        """
        Add separator QAction to the menu.
        
        :return: Separator
        :rtype: QAction
        """
        separator = utils.QAction(self.menu)
        separator.setSeparator( True )
        
        self.menu.addAction(separator)
        self.buttons.append(separator)
        return separator
        
    def addButton(self, text, command=None):
        """
        Add button QAction to the menu.
        
        :param str text: Button text
        :param func command: Function to call when button is released.
        :return: Button
        :rtype: QAction
        """
        button = utils.QAction(self.menu)
        button.setText(text)
        
        if command:
            button.triggered.connect(command)
        
        self.menu.addAction(button) 
        self.buttons.append(button)        
        return button
       
    # ------------------------------------------------------------------------
        
    def picker( self ):
        """
        The picker will change the color of the button and will store the 
        rgb values in a property, this property will be read when a marker is 
        added via the menu.
        """
        rgbL = self.colorA.property("rgb")
        rgbQt = utils.QColor(rgbL[0], rgbL[1], rgbL[2])
        
        dialog = utils.QColorDialog.getColor(rgbQt, self.menu)
        if not dialog.isValid():
            return
            
        rgb = [dialog.red(), dialog.green(), dialog.blue()]

        pixmap = utils.QPixmap(12, 12)
        pixmap.fill(utils.QColor(rgb[0], rgb[1], rgb[2]))
        
        self.colorA.setProperty("rgb", rgb)
        self.colorA.setIcon(utils.QIcon(pixmap))
            
    # ------------------------------------------------------------------------
        
    def deleteLater(self):
        """
        Remove all marker related QActions from the timeline menu.
        """
        for button in self.buttons:
            button.deleteLater()
            
            
def install():
    """
    Add the marker functionality to Maya's native timeline menu. 
    
    :raises RuntimeError: When the timeline marker is already installed.
    """
    global TIMELINE_MARKER
    
    # validate timeline marker
    if TIMELINE_MARKER:
        raise RuntimeError("Timeline marker is already installed!")
    
    # get parent
    parent = utils.getTimeline()
    layout = parent.layout()
    
    # create layout if non exists
    if not layout:
        layout = utils.QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        parent.setLayout(layout)
    
    # create timeline marker
    TIMELINE_MARKER = TimelineMarker()
    TIMELINE_MARKER.setParent(parent)
    layout.addWidget(TIMELINE_MARKER)
