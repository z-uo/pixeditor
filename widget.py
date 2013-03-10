#!/usr/bin/env python
#-*- coding: utf-8 -*-


import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt

class Button(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setFixedSize(24, 24)
        self.pressed = False
        icon = QtGui.QPixmap("icons/frame_add_anim.png")
        self.li = []
        for i in range(0, icon.height(),24):
            self.li.append(icon.copy(0, i, 24, 24))
        self.pix = self.li[0]
        
    def paintEvent(self, ev=None):
        p = QtGui.QPainter(self)
        p.drawPixmap(0, 0, self.pix)
        
    def mousePressEvent(self, event):
        if self.pressed == False:
            self.pix = self.li[1]
            self.pressed = True
        self.update()
    def enterEvent(self, event):
        if self.pressed == False:
            self.pix = self.li[1]
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.anim)
            self.i = 0
            self.timer.start(100)
        self.update()
    def leaveEvent(self, event):
        if self.pressed == False:
            self.timer.stop()
            self.pix = self.li[0]
        self.update()
    def anim(self):
        self.i = (self.i+1) % len(self.li)
        print self.i
        self.pix = self.li[self.i]
        self.update()
