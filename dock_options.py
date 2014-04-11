#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from PyQt4 import QtCore
from PyQt4 import QtGui

from widget import Button


class ColorWidget(QtGui.QWidget):
    """ widget for alpha and current color, select on clic"""
    def __init__(self, color, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setFixedSize(26, 26)
        self.background = QtGui.QBrush(self.parent.project.bgColor)
        self.alpha = QtGui.QPixmap("icons/color_alpha.png")
        self.parent.project.updateBackgroundSign.connect(self.updateBackground)
        self.color = color
        self.parent.project.updatePaletteSign.connect(self.update)
        if color:
            self.setToolTip("current color (E)")
        else:
            self.setToolTip("alpha color (E)")
        
    def updateBackground(self):
         self.background = QtGui.QBrush(self.parent.project.bgColor)
         self.update()

    def event(self, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress and
                       event.button()==QtCore.Qt.LeftButton):
            if self.color:
                self.parent.project.changeColor(self.parent.project.currentColor)
            else:
                self.parent.project.changeColor(0)
        elif event.type() == QtCore.QEvent.Paint:
            col, cur = self.parent.project.color, self.parent.project.currentColor
            p = QtGui.QPainter(self)
            p.fillRect (0, 0, self.width(), self.height(), 
                    QtGui.QBrush(QtGui.QColor(70, 70, 70)))
            p.fillRect (1, 1, self.width()-2, self.height()-2, self.background)
            if ((not self.color and self.parent.project.color == 0)
                or (self.color and col == cur)):
                p.fillRect (3, 3, 20, 20, QtGui.QBrush(QtGui.QColor(0, 0, 0)))
                p.fillRect (4, 4, 18, 18, QtGui.QBrush(QtGui.QColor(255, 255, 255)))
            if self.color:
                p.fillRect(5, 5, 16, 16, QtGui.QBrush(
                    QtGui.QColor().fromRgba(self.parent.project.colorTable[self.parent.project.currentColor])))
            else:
                p.drawPixmap(5, 5, self.alpha)
                # just to be sure alpha is the first color
                p.fillRect(5, 5, 16, 16, QtGui.QBrush(
                    QtGui.QColor().fromRgba(self.parent.project.colorTable[0])))
        return QtGui.QWidget.event(self, event)

    
class PenWidget(QtGui.QWidget):
    """ widget for pen, menu on clic """
    def __init__(self, parent, project):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.project = project
        self.setToolTip("pen")
        self.setFixedSize(26, 26)
        self.project.updateBackgroundSign.connect(self.update)
        self.penMenu = QtGui.QMenu(self)
        self.currentAction = None
        self.loadPen()
        self.project.customPenSign.connect(self.setCustomPen)

    def loadPen(self):
        self.penMenu.clear()
        for name, icon in self.project.penList:
            action = QtGui.QAction(QtGui.QIcon(icon), name, self)
            action.pixmap = icon
            action.setIconVisibleInMenu(True)
            self.penMenu.addAction(action)
            if not self.currentAction:
                self.currentAction = action

    def event(self, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.changePen()
        elif event.type() == QtCore.QEvent.Paint:
            p = QtGui.QPainter(self)
            p.fillRect (0, 0, self.width(), self.height(), 
                    QtGui.QBrush(QtGui.QColor(70, 70, 70)))
            p.fillRect (1, 1, self.width()-2, self.height()-2, 
                    QtGui.QBrush(self.project.bgColor))
            if self.currentAction.pixmap:
                p.drawPixmap(5, 5, self.currentAction.pixmap)
        return QtGui.QWidget.event(self, event)
        
    def changePen(self):
        self.penMenu.setActiveAction(self.currentAction)
        action = self.penMenu.exec(self.mapToGlobal(QtCore.QPoint(26, 2)), self.currentAction)
        if action:
            self.currentAction = action
            self.project.pen = self.project.penDict[action.text()]
            self.project.penChangedSign.emit()
            self.update()
        
    def setCustomPen(self, li):
        nLi = []
        mY = len(li)//2
        mX = len(li[0])//2
        for y in range(len(li)):
            py = y - mY
            for x in range(len(li[y])):
                col = li[y][x]
                if col:
                    px = x - mX
                    nLi.append((px, py, col))
        if nLi:
            self.project.penDict["custom"] = nLi
            self.project.pen = self.project.penDict["custom"]
            self.icon = None
            self.update()
            self.project.toolSetPenSign.emit()


class BrushWidget(QtGui.QWidget):
    """ widget for brush, menu on clic """
    def __init__(self, parent, project):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.project = project
        self.setToolTip("brush")
        self.setFixedSize(26, 26)
        self.project.updateBackgroundSign.connect(self.update)
        self.brushMenu = QtGui.QMenu(self)
        self.currentAction = None
        self.loadBrush()

    def loadBrush(self):
        self.brushMenu.clear()
        for name, icon in self.project.brushList:
            action = QtGui.QAction(QtGui.QIcon(icon), name, self)
            action.pixmap = icon
            action.setIconVisibleInMenu(True)
            self.brushMenu.addAction(action)
            if name == "solid":
                self.currentAction = action

    def event(self, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.changeBrush()
        elif event.type() == QtCore.QEvent.Paint:
            p = QtGui.QPainter(self)
            p.fillRect (0, 0, self.width(), self.height(), 
                    QtGui.QBrush(QtGui.QColor(70, 70, 70)))
            p.fillRect (1, 1, self.width()-2, self.height()-2, 
                    QtGui.QBrush(self.project.bgColor))
            if self.currentAction.pixmap:
                p.drawPixmap(5, 5, self.currentAction.pixmap)
        return QtGui.QWidget.event(self, event)
        
    def changeBrush(self):
        self.brushMenu.setActiveAction(self.currentAction)
        action = self.brushMenu.exec(self.mapToGlobal(QtCore.QPoint(26, 2)), self.currentAction)
        if action:
            self.currentAction = action
            self.project.brush = self.project.brushDict[action.text()]
            self.update()

            
class OptionFill(QtGui.QWidget):
    """ contextual option for the fill tool """
    def __init__(self, parent, project):
        QtGui.QVBoxLayout .__init__(self)
        self.project = project
        self.parent = parent
        
        self.adjacentFillRadio = QtGui.QRadioButton("adjacent colors", self)
        self.adjacentFillRadio.pressed.connect(self.adjacentPressed)
        self.adjacentFillRadio.setChecked(True)
        self.similarFillRadio = QtGui.QRadioButton("similar colors", self)
        self.similarFillRadio.pressed.connect(self.similarPressed)
        
        ### Layout ###
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self.adjacentFillRadio)
        layout.addWidget(self.similarFillRadio)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
    def adjacentPressed(self):
        self.project.fillMode = "adjacent"
        
    def similarPressed(self):
        self.project.fillMode = "similar"
        
        
class OptionSelect(QtGui.QWidget):
    """ contextual option for the select tool """
    def __init__(self, parent, project):
        QtGui.QVBoxLayout .__init__(self)
        self.project = project
        
        self.cutFillRadio = QtGui.QRadioButton("cut", self)
        self.cutFillRadio.pressed.connect(self.cutPressed)
        self.cutFillRadio.setChecked(True)
        self.copyFillRadio = QtGui.QRadioButton("copy", self)
        self.copyFillRadio.pressed.connect(self.copyPressed)
        
        ### Layout ###
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self.cutFillRadio)
        layout.addWidget(self.copyFillRadio)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
    def cutPressed(self):
        self.project.selectMode = "cut"
    
    def copyPressed(self):
        self.project.selectMode = "copy"


class OptionMove(QtGui.QWidget):
    """ contextual option for the select tool """
    def __init__(self, parent, project):
        QtGui.QVBoxLayout .__init__(self)
        self.project = project
        
        self.noWrapRadio = QtGui.QRadioButton("no wrap", self)
        self.noWrapRadio.pressed.connect(self.noWrapPressed)
        self.noWrapRadio.setChecked(True)
        self.wrapRadio = QtGui.QRadioButton("wrap", self)
        self.wrapRadio.pressed.connect(self.wrapPressed)
        
        ### Layout ###
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self.noWrapRadio)
        layout.addWidget(self.wrapRadio)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
    def noWrapPressed(self):
        self.project.moveMode = "no_wrap"
    
    def wrapPressed(self):
        self.project.moveMode = "wrap"


class OptionsWidget(QtGui.QWidget):
    """ widget cantaining options """
    def __init__(self, project):
        QtGui.QWidget.__init__(self)
        self.project = project

        self.penWidget = PenWidget(self, self.project)
        self.brushWidget = BrushWidget(self, self.project)
        self.alphaWidget = ColorWidget(False, self)
        self.colorWidget = ColorWidget(True, self)
        self.onionSkinB = Button("onion skin",
            "icons/onionskin_prev.png", self.onionskinClicked, True)
        
        self.optionFill = OptionFill(self, self.project)
        self.optionMove = OptionMove(self, self.project)
        self.optionSelect = OptionSelect(self, self.project)
        self.project.toolChangedSign.connect(self.toolChanged)

        ### Layout ###
        context = QtGui.QHBoxLayout()
        context.setSpacing(8)
        context.addWidget(self.alphaWidget)
        context.addWidget(self.colorWidget)
        context.addStretch()
        context.addWidget(self.onionSkinB)
        context.addStretch()
        context.addWidget(self.penWidget)
        context.addWidget(self.brushWidget)
        context.setContentsMargins(0, 0, 0, 0)
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(4)
        layout.addLayout(context)
        layout.addWidget(self.optionFill)
        self.optionFill.hide()
        layout.addWidget(self.optionMove)
        self.optionMove.hide()
        layout.addWidget(self.optionSelect)
        self.optionSelect.hide()
        layout.addStretch()
        
        self.setLayout(layout)
        
    def toolChanged(self):
        if self.project.tool == "fill":
            self.optionSelect.hide()
            self.optionMove.hide()
            self.optionFill.show()
        elif self.project.tool == "move":
            self.optionFill.hide()
            self.optionSelect.hide()
            self.optionMove.show()
        elif self.project.tool == "select":
            self.optionFill.hide()
            self.optionMove.hide()
            self.optionSelect.show()
        else:
            self.optionFill.hide()
            self.optionMove.hide()
            self.optionSelect.hide()
            
    def onionskinClicked(self):
        self.project.onionSkin["check"] = self.onionSkinB.isChecked()
        self.project.updateViewSign.emit()
