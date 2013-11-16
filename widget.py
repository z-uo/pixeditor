#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Python 3 Compatibility
from __future__ import division
from __future__ import print_function

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt

    
class Dock(QtGui.QDockWidget):
    """ dock """
    def __init__(self, title, parent=None, flags=QtCore.Qt.WindowFlags(0)):
        QtGui.QDockWidget.__init__(self, title, parent, flags)
        self.setTitleBarWidget(QtGui.QWidget())
        self.setTitleBarWidget(None)
        orientation = Qt.Qt.Orientation(Qt.Qt.Horizontal)
    
class Button(QtGui.QToolButton):
    """ button """
    def __init__(self, tooltip, iconUrl, connection, checkable=False):
        QtGui.QToolButton.__init__(self)
        self.setToolTip(tooltip)
        self.setAutoRaise(True)
        self.setCheckable(checkable)
        self.setIconSize(QtCore.QSize(24, 24)) 
        self.setIcon(QtGui.QIcon(QtGui.QPixmap(iconUrl)))
        self.clicked.connect(connection)


class Background(QtGui.QPixmap):
    """ background of the scene"""
    def __init__(self, size, arg=16):
        QtGui.QPixmap.__init__(self, size)
        self.fill(QtGui.QColor(0, 0, 0, 0))
        if type(arg) is int and arg:
            p = QtGui.QPainter(self)
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 30))
            bol = True
            for x in range(0, size.width(), arg):
                for y in range(0, size.height(), arg*2):
                    if bol:
                        p.fillRect (x, y, arg, arg, brush)
                    else:
                        p.fillRect (x, y+arg, arg, arg, brush)
                bol = not bol
        elif type(arg) is str:
            brush = QtGui.QBrush(QtGui.QPixmap(arg))
            p = QtGui.QPainter(self)
            p.fillRect (0, 0, size.width(), size.height(), brush)


class Viewer(QtGui.QScrollArea):
    """ QScrollArea you can move with midbutton"""
    resyzing = QtCore.pyqtSignal(tuple)
    def __init__ (self):
        QtGui.QScrollArea.__init__(self)
        
    def event(self, event):
        """ capture middle mouse event to move the view """
        # clic: save position
        if   (event.type() == QtCore.QEvent.MouseButtonPress and
              event.button() == QtCore.Qt.MidButton):
            self.mouseX, self.mouseY = event.x(), event.y()
            return True
        # drag: move the scrollbars
        elif (event.type() == QtCore.QEvent.MouseMove and
              event.buttons() == QtCore.Qt.MidButton):
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - (event.x() - self.mouseX))
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - (event.y() - self.mouseY))
            self.mouseX, self.mouseY = event.x(), event.y()
            return True
        elif (event.type() == QtCore.QEvent.Resize):
            self.resyzing.emit((event.size().width(), event.size().height()))
        return QtGui.QScrollArea.event(self, event)
