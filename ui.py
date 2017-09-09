import json
from maya import OpenMaya, OpenMayaUI, cmds, mel

# import pyside, do qt version check for maya 2017 >
qtVersion = cmds.about(qtVersion=True)
if qtVersion.startswith("4"):
    from PySide.QtGui import *
    from PySide.QtCore import *
    import shiboken
else:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    import shiboken2 as shiboken
    
# ----------------------------------------------------------------------------    
    
def mayaToQT(name):
    """
    Maya -> QWidget

    :param str name: Maya name of an ui object
    :return: QWidget of parsed Maya name
    :rtype: QWidget
    """
    ptr = OpenMayaUI.MQtUtil.findControl(name)
    if ptr is None:         
        ptr = OpenMayaUI.MQtUtil.findLayout(name)    
    if ptr is None:         
        ptr = OpenMayaUI.MQtUtil.findMenuItem(name)
    if ptr is not None:     
        return shiboken.wrapInstance(long(ptr), QWidget)

# ----------------------------------------------------------------------------

def getMayaTimeline():
    """
    Get the object name of Maya's timeline.
    
    :return: Object name of Maya's timeline
    :rtype: str
    """
    return mel.eval("$tmpVar=$gPlayBackSlider")

def getTimeline():
    """
    Get the QWidget of Maya's timeline. For versions 2016.5 and later the 
    first QWidget child of the timeline should be returned.
    
    :return: QWidget of Maya's timeline
    :rtype: QWidget
    """
    # convert name to widget
    qtTimeline = mayaToQT(getMayaTimeline())
    
    # return child for Maya 2016.5 > 
    for child in qtTimeline.children():
        if type(child) == QWidget:
            return child
    
    return qtTimeline

def getTimelineMenu():
    """
    Get the QWidget of Maya's timeline menu. An initialization mel function
    has to be called to create and populate the menu before adding 
    functionality.
    
    :return: QWidget of Maya's timeline menu
    :rtype: QWidget
    """
    # initialize timeline menu
    mel.eval("updateTimeSliderMenu TimeSliderMenu;")
    
    # get time slider menu
    qtTimelineMenu = mayaToQT("TimeSliderMenu")
    return qtTimelineMenu
    
def getTimelineRange():
    """
    Read the current timeline selection and convert it into a range list.

    :return: Frame range of timeline selection
    :rtype: list
    """
    r = cmds.timeControl(getMayaTimeline(), query=True, ra=True )
    return range(int(r[0]), int(r[1]))

# ----------------------------------------------------------------------------

def remap(value, oMin, oMax, nMin, nMax):
    """
    Remap a value based on input minimin and maximum, the result is converted
    to an integer since markers can only live as a whole frame.
    
    :param float value: Value to remap
    :param float oMin: Original minimum
    :param float oMax: Original maximum
    :param float nMin: New minimum
    :param float nMax: New maximum
    :return: remapped value
    :rtype: int
    """
    return int((((value - oMin) * (nMax - nMin)) / (oMax - oMin)) + nMin)

# ----------------------------------------------------------------------------
    
class TimelineMarker(QWidget):
    def __init__(self, parent=getTimeline()):
        QWidget.__init__(self, parent)
        
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
        
        # get layout
        layout = parent.layout()

        # create layout if non exists
        if not layout:
            layout = QVBoxLayout(parent)
            layout.setContentsMargins(0, 0, 0, 0)
            parent.setLayout(layout)

        # find and remove timelineMarker instances
        for child in parent.children():
            if child.objectName() == "timelineMarkers":
                child.menu.deleteLater()
                child.deleteLater()
                    
        # add self to parent layout
        layout.addWidget(self)
        self.setObjectName("timelineMarkers") 

        # set menu
        self.menu = TimelineMarkerMenu(self)

        # initialize
        self.readFromCurrentScene()
        self.addCallbacks()

        print "Timeline Marker: installation succeeded"
   
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
        if event.type() == QEvent.ToolTip:
            QToolTip.hideText() 
            
            # find frame at mouse pointer
            frame = int(((event.x()-(self.total*0.005))/self.step)+self.start)
            
            # get comment for frame
            _, _, _, comment = self.getDataFromFrame(frame)
            
            # show tooltip
            QToolTip.showText(event.globalPos(), comment, self)
            
        return QWidget.event(self, event)
        
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
        for f in getTimelineRange():
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
        for f in getTimelineRange():
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
        # get visible range
        rangeVisible = cmds.timeControl(
            getMayaTimeline(), 
            q=True, 
            rangeVisible=True
        )
        
        # check if range needs to be stored
        if not rangeVisible or not self.menu.moveA.isChecked():
            return

        # save range
        self._range = getTimelineRange()

    def releaseCommand(self, *args):
        """
        Release callback on the timeline, together with the press command the
        difference can be extracted and the markers can be moved accordingly. 
        Theuser settings will be checked if the moving of markers is 
        appropriate.
        """
        # check if markers need to be shifted
        if not self._range or not self.menu.moveA.isChecked():
            return

        # get begin and end range
        beginRange = self._range[:]
        endRange = getTimelineRange()

        # reset stored range
        self._range = None

        # check data
        beginLength = len(beginRange)
        endLenght = len(endRange)
        
        rangeVisible = cmds.timeControl(
            getMayaTimeline(), 
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
                remappedFrame = remap(
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
        Take all the marker information and fill in the QWidget covering the 
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
        painter = QPainter(self)
        pen = QPen()
        pen.setWidth(self.step)
            
        # draw Lines for each frame
        for f, c in zip(self.frames, self.colors):
            pen.setColor(QColor(c[0], c[1], c[2], 50))
        
            # calculate line position
            pos = (f-self.start+0.5) * self.step + (self.total*0.005)
            line = QLineF(QPointF(pos, 0), QPointF(pos, 100))
            
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
            getMayaTimeline(), 
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
            getMayaTimeline(), 
            edit=True, 
            pressCommand="", 
            releaseCommand=""
        )
        
    # ------------------------------------------------------------------------
    
    def update(self):
        """
        Subclass update to simultaniously store all of the marker data into
        the current scene.
        """
        self.saveToCurrentScene()
        QWidget.update(self)
        
    def deleteLater(self):
        """
        Subclass the deleteLater function to first remove the callback, 
        this callback shouldn't be floating around and should be deleted
        with the widget.
        """
        self.removeCallbacks()
        QWidget.deleteLater(self)

class TimelineMarkerMenu(object):
    def __init__(self, parent, menu=getTimelineMenu()):    
        # variable
        self.menu = menu
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
        edit = QLineEdit(self.menu)
        edit.setPlaceholderText(placeholderText)
        
        button = QWidgetAction(self.menu)
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
        
        pixmap = QPixmap(12, 12)
        pixmap.fill(QColor(0, 255, 0))
        
        button.setIcon(QIcon(pixmap))
        return button
        
    # ------------------------------------------------------------------------
    
    def addSeparator(self):
        """
        Add seperator QAction to the menu.
        
        :return: Seperator
        :rtype: QAction
        """
        separator = QAction(self.menu)
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
        button = QAction(self.menu)
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
        rgbQt = QColor(rgbL[0], rgbL[1], rgbL[2])
        
        dialog = QColorDialog.getColor(rgbQt, self.menu)
        if not dialog.isValid():
            return
            
        rgb = [dialog.red(), dialog.green(), dialog.blue()]

        pixmap = QPixmap(12, 12)
        pixmap.fill(QColor(rgb[0], rgb[1], rgb[2]))
        
        self.colorA.setProperty("rgb", rgb)
        self.colorA.setIcon(QIcon(pixmap))
            
    # ------------------------------------------------------------------------
        
    def deleteLater(self):
        """
        Remove all marker related QActions from the timeline menu.
        """
        for button in self.buttons:
            button.deleteLater()
            