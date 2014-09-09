#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from PyQt4 import QtCore
from PyQt4 import QtGui

from widget import Button, Viewer
from colorPicker import ColorDialog


class PaletteCanvas(QtGui.QWidget):
    """ Canvas where the palette is draw """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setFixedSize(164, 644)
        self.background = QtGui.QBrush(self.parent.project.bgColor)
        self.black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        self.white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        self.parent.project.updateBackgroundSign.connect(self.updateBackground)
        
    def updateBackground(self):
         self.background = QtGui.QBrush(self.parent.project.bgColor)
         self.update()
         
    def paintEvent(self, ev=''):
        p = QtGui.QPainter(self)
        p.fillRect (0, 0, self.width(), self.height(), self.background)
        usedColorIndexTable=self.parent.project.getUsedColorList()
        for n, i in enumerate(self.parent.project.colorTable):
            if n > 0:
                y = (((n-1) // 8) * 20) + 2
                x = (((n-1) % 8) * 20) + 2
                if n == self.parent.project.color:
                    p.fillRect (x-1, y-1, 22, 22, self.white)
                    p.fillRect (x+1, y+1, 18, 18, self.black)
                if (n in usedColorIndexTable):
                    p.fillRect (x+1, y+1, 18, 18, self.white)
                p.fillRect(x+2, y+2, 16, 16, QtGui.QBrush(QtGui.QColor().fromRgba(i)))

    def event(self, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress and
                       event.button()==QtCore.Qt.LeftButton):
            item = self.getItem(event.x(), event.y())
            if item is not None:
                self.parent.project.changeColor(item)
        elif (event.type() == QtCore.QEvent.MouseButtonDblClick and
                       event.button()==QtCore.Qt.LeftButton):
            item = self.getItem(event.x(), event.y())
            if item is not None:
                self.parent.editColor(item)
        return QtGui.QWidget.event(self, event)
        
    def getItem(self, x, y):
        x, y = ((x-2) // 20), ((y-2) // 20)
        if y == 0:
            s = x + 1
        else:
            s = (y * 8) + x + 1
        if s >= 0 and s < len(self.parent.project.colorTable):
            return s
        return None


class PaletteWidget(QtGui.QWidget):
    """ widget containing palette """
    def __init__(self, project):
        QtGui.QWidget.__init__(self)
        self.project = project
        ### palette ###
        self.paletteCanvas = PaletteCanvas(self)
        self.paletteV = Viewer()
        self.paletteV.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.paletteV.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.paletteV.setWidget(self.paletteCanvas)
        ### buttons ###
        self.project.updatePaletteSign.connect(self.paletteCanvas.update)
        addColorB = Button("add color", "icons/color_add.png", self.addColor)
        delColorB = Button("delete color", "icons/color_del.png", self.delColor)
        moveLeftColorB = Button("move color left", "icons/color_move_left.png", self.moveColorLeft)
        moveRightColorB = Button("move color right", "icons/color_move_right.png", self.moveColorRight)
        ### layout ###
        colorButtons = QtGui.QHBoxLayout()
        colorButtons.setSpacing(0)
        colorButtons.addWidget(addColorB)
        colorButtons.addWidget(delColorB)
        colorButtons.addWidget(moveLeftColorB)
        colorButtons.addWidget(moveRightColorB)
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.addWidget(self.paletteV)
        self.layout.addLayout(colorButtons)
        self.layout.setContentsMargins(6, 0, 6, 0)
        self.setLayout(self.layout)

    def showEvent(self, event):
        self.paletteV.setFixedWidth(self.paletteCanvas.width() + 
                    self.paletteV.verticalScrollBar().width() + 2)

    def editColor(self, n):
        col = self.project.colorTable[self.project.color]
        ok, color = ColorDialog(False, col).getRgb()
        if not ok:
            return
        self.project.saveToUndo("colorTable")
        self.project.colorTable[n] = color
        for i in self.project.timeline.getAllCanvas():
            i.setColorTable(self.project.colorTable)
        self.project.updateViewSign.emit()
        self.paletteCanvas.update()
        self.project.colorChangedSign.emit()

    def addColor(self):
        """ choose a color and add it to the palette """
        if not len(self.project.colorTable) >= 256:
            col = self.project.colorTable[self.project.color]
            ok, color = ColorDialog(False, col).getRgb()
            if not ok:
                return
            self.project.saveToUndo("colorTable_frames")
            self.project.colorTable.append(color)
            self.project.changeColor(len(self.project.colorTable)-1)
            for i in self.project.timeline.getAllCanvas():
                i.setColorTable(self.project.colorTable)
            self.project.updateViewSign.emit()

    def delColor(self):
        """ delete a color, replace with color 0 on canvas """
        col, table = self.project.color, self.project.colorTable
        if col != 0:
            self.project.saveToUndo("colorTable_frames")
            table.pop(col)
            for i in self.project.timeline.getAllCanvas():
                i.delColor(col)
                i.setColorTable(table)
            self.project.changeColor(col-1)
            self.project.updateViewSign.emit()

    def moveColorLeft(self):
        col, table = self.project.color, self.project.colorTable
        if col != 0 and col != 1:
            self.project.saveToUndo("colorTable_frames")
            table[col], table[col-1] = table[col-1], table[col]
            for i in self.project.timeline.getAllCanvas():
                i.swapColor(col, col-1)
                i.setColorTable(table)
            self.project.changeColor(col-1)

    def moveColorRight(self):
        col, table = self.project.color, self.project.colorTable
        if col != len(table)-1 and col != 0:
            self.project.saveToUndo("colorTable_frames")
            table[col], table[col+1] = table[col+1], table[col]
            for i in self.project.timeline.getAllCanvas():
                i.swapColor(col, col+1)
                i.setColorTable(table)
            self.project.changeColor(col+1)
