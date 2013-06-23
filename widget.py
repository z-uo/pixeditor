#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Python 3 Compatibility
from __future__ import division
from __future__ import print_function

from PyQt4 import QtCore
from PyQt4 import QtGui

    
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
