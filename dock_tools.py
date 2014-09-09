#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from PyQt4 import QtCore
from PyQt4 import QtGui

from widget import Button, Label


class ToolsWidget(QtGui.QWidget):
    """ widget cantaining tools buttons """
    def __init__(self, project):
        QtGui.QWidget.__init__(self)
        self.project = project
        ### coordinates ###
        self.coords = Label("Cursor coordinates")
        self.coords.setText("x\ny");
        ### tools buttons ###
        self.penB = Button("pen (1)", "icons/tool_pen.png", self.penClicked, True)
        self.penB.setChecked(True)
        self.project.toolSetPenSign.connect(self.penClicked)
        self.pipetteB = Button("pipette (2)", "icons/tool_pipette.png", self.pipetteClicked, True)
        self.fillB = Button("fill (3)", "icons/tool_fill.png", self.fillClicked, True)
        self.moveB = Button("move (4)", "icons/tool_move.png", self.moveClicked, True)
        self.selectB = Button("select (5)", "icons/tool_select.png", self.selectClicked, True)
        ### Layout ###
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self.coords)
        layout.addWidget(self.penB)
        layout.addWidget(self.pipetteB)
        layout.addWidget(self.fillB)
        layout.addWidget(self.moveB)
        layout.addWidget(self.selectB)
        layout.addStretch()
        layout.setContentsMargins(6, 0, 6, 0)
        self.setLayout(layout)
        
    def penClicked(self):
        self.project.tool = "pen"
        self.penB.setChecked(True)
        self.pipetteB.setChecked(False)
        self.fillB.setChecked(False)
        self.moveB.setChecked(False)
        self.selectB.setChecked(False)
        self.project.toolChangedSign.emit()

    def pipetteClicked(self):
        self.project.tool = "pipette"
        self.penB.setChecked(False)
        self.fillB.setChecked(False)
        self.pipetteB.setChecked(True)
        self.moveB.setChecked(False)
        self.selectB.setChecked(False)
        self.project.toolChangedSign.emit()

    def fillClicked(self):
        self.project.tool = "fill"
        self.fillB.setChecked(True)
        self.pipetteB.setChecked(False)
        self.penB.setChecked(False)
        self.moveB.setChecked(False)
        self.selectB.setChecked(False)
        self.project.toolChangedSign.emit()

    def moveClicked(self):
        self.project.tool = "move"
        self.fillB.setChecked(False)
        self.pipetteB.setChecked(False)
        self.penB.setChecked(False)
        self.moveB.setChecked(True)
        self.selectB.setChecked(False)
        self.project.toolChangedSign.emit()
        
    def selectClicked(self):
        self.project.tool = "select"
        self.fillB.setChecked(False)
        self.pipetteB.setChecked(False)
        self.penB.setChecked(False)
        self.moveB.setChecked(False)
        self.selectB.setChecked(True)
        self.project.toolChangedSign.emit()
