import shiboken2
from six import integer_types
from maya import mel
from maya import cmds
from maya import OpenMayaUI
from PySide2 import QtWidgets, QtCore


def maya_to_qt(name, type_=QtWidgets.QWidget):
    """
    :param str name: Maya path of an ui object
    :param cls type_:
    :return: QWidget of parsed Maya path
    :rtype: QWidget
    :raise RuntimeError: When no handle could be obtained
    """
    ptr = OpenMayaUI.MQtUtil.findControl(name)
    if ptr is None:
        ptr = OpenMayaUI.MQtUtil.findLayout(name)
    if ptr is None:
        ptr = OpenMayaUI.MQtUtil.findMenuItem(name)
    if ptr is not None:
        ptr = integer_types[-1](ptr)
        return shiboken2.wrapInstance(ptr, type_)

    raise RuntimeError("Failed to obtain a handle to '{}'.".format(name))

        
# ----------------------------------------------------------------------------


def get_timeline_path():
    """
    :return: Object path of Maya's timeline
    :rtype: str
    """
    return mel.eval("$tmpVar=$gPlayBackSlider")

    
def get_timeline():
    """
    Get the QWidget of Maya's timeline. For versions 2016.5 and later the 
    first QWidget child of the timeline should be returned.
    
    :return: QWidget of Maya's timeline
    :rtype: QtWidgets.QWidget
    """
    # convert name to widget
    timeline_path = get_timeline_path()
    timeline = maya_to_qt(timeline_path)
    
    # return child for Maya 2016.5 > 
    for child in timeline.children():
        if isinstance(child, QtWidgets.QWidget):
            return child
    
    return timeline

    
def get_timeline_menu():
    """
    Get the QWidget of Maya's timeline menu. An initialization mel function
    has to be called to create and populate the menu before adding 
    functionality.
    
    :return: QWidget of Maya's timeline menu
    :rtype: QtWidget.QMenu
    """
    mel.eval("updateTimeSliderMenu TimeSliderMenu;")
    return maya_to_qt("TimeSliderMenu", QtWidgets.QMenu)

    
def get_timeline_range():
    """
    :return: Frame range of timeline selection
    :rtype: list[int]
    """
    timeline_path = get_timeline_path()
    timeline_range = cmds.timeControl(timeline_path, query=True, rangeArray=True)
    return range(int(timeline_range[0]), int(timeline_range[1]))

    
# ----------------------------------------------------------------------------


def remap(value, input_min, input_max, output_min, output_max):
    """
    Remap a value based on input minimum and maximum, the result is converted
    to an integer since markers can only live as a whole frame.
    
    :param float value: Value to remap
    :param float input_min: Original minimum
    :param float input_max: Original maximum
    :param float output_min: New minimum
    :param float output_max: New maximum
    :return: Remapped value
    :rtype: int
    """
    return (((value - input_min) * (output_max - output_min)) / (input_max - input_min)) + output_min
