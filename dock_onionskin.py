#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from PyQt4 import QtCore
from PyQt4 import QtGui

from widget import Button
from colorPicker import ColorDialog
"""
        self.onionSkin = {"check"      : False,
                          "color"      : False,
                          "prev_color" : QtGui.QColor(255, 0, 0),
                          "prev"       : [[True, 0.5], [False, 0.25], [False, 0.125]],
                          "next_color" : QtGui.QColor(0, 0, 255),
                          "next"       : [[True, 0.5], [False, 0.25], [False, 0.125]]}
"""
class OnionSkinWidget(QtGui.QWidget):
    def __init__(self, project):
        QtGui.QWidget.__init__(self)
        self.project = project
        
        # color
        self.prevcolorIcon = QtGui.QPixmap(32, 16)
        self.prevcolorIcon.fill(self.project.onionSkin["prev_color"])
        self.colorPrevB = Button("previous frames color",
            QtGui.QIcon(self.prevcolorIcon), self.prevColorChanged)
        self.colorPrevB.setIconSize(QtCore.QSize(36, 20))
        
        self.colorCheck = QtGui.QCheckBox(self)
        self.colorCheck.setToolTip("colored onion skin")
        self.colorCheck.setChecked(self.project.onionSkin["color"])
        self.colorCheck.stateChanged.connect(self.checkColor)
        
        self.nextcolorIcon = QtGui.QPixmap(32, 16)
        self.nextcolorIcon.fill(self.project.onionSkin["next_color"])
        self.colorNextB = Button("next frames color",
            QtGui.QIcon(self.nextcolorIcon), self.nextColorChanged)
        self.colorNextB.setIconSize(QtCore.QSize(36, 20))
        
        # onionskin
        prev = self.project.onionSkin["prev"]
        self.prev1Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.prev1Slider.setRange(0, 100)
        self.prev1Slider.setValue(prev[0][1] * 100)
        self.prev1Slider.valueChanged.connect(self.valueChanged)
        self.prev1Check = QtGui.QCheckBox(self)
        self.prev1Check.setChecked(prev[0][0])
        self.prev1Check.stateChanged.connect(self.valueChanged)
        self.prev2Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.prev2Slider.setRange(0, 100)
        self.prev2Slider.setValue(prev[1][1] * 100)
        self.prev2Slider.valueChanged.connect(self.valueChanged)
        self.prev2Check = QtGui.QCheckBox(self)
        self.prev2Check.setChecked(prev[1][0])
        self.prev2Check.stateChanged.connect(self.valueChanged)
        self.prev3Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.prev3Slider.setRange(0, 100)
        self.prev3Slider.setValue(prev[2][1] * 100)
        self.prev3Slider.valueChanged.connect(self.valueChanged)
        self.prev3Check = QtGui.QCheckBox(self)
        self.prev3Check.setChecked(prev[2][0])
        self.prev3Check.stateChanged.connect(self.valueChanged)
        
        self.currentSlider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.currentSlider.setRange(0, 100)
        self.currentSlider.setValue(100)
        self.currentSlider.setDisabled(True)
        self.currentSlider.setMinimumHeight(100)
        
        nex = self.project.onionSkin["next"]
        self.next1Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.next1Slider.setRange(0, 100)
        self.next1Slider.setValue(nex[0][1] * 100)
        self.next1Slider.valueChanged.connect(self.valueChanged)
        self.next1Check = QtGui.QCheckBox(self)
        self.next1Check.setChecked(nex[0][0])
        self.next1Check.stateChanged.connect(self.valueChanged)
        self.next2Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.next2Slider.setRange(0, 100)
        self.next2Slider.setValue(nex[1][1] * 100)
        self.next2Slider.valueChanged.connect(self.valueChanged)
        self.next2Check = QtGui.QCheckBox(self)
        self.next2Check.setChecked(nex[1][0])
        self.next2Check.stateChanged.connect(self.valueChanged)
        self.next3Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.next3Slider.setRange(0, 100)
        self.next3Slider.setValue(nex[2][1] * 100)
        self.next3Slider.valueChanged.connect(self.valueChanged)
        self.next3Check = QtGui.QCheckBox(self)
        self.next3Check.setChecked(nex[2][0])
        self.next3Check.stateChanged.connect(self.valueChanged)
        
        # layout
        colorLayout = QtGui.QHBoxLayout()
        colorLayout.setSpacing(0)
        colorLayout.addWidget(self.colorPrevB)
        colorLayout.addStretch()
        colorLayout.addWidget(self.colorCheck)
        colorLayout.addStretch()
        colorLayout.addWidget(self.colorNextB)
        sliderLayout = QtGui.QGridLayout()
        sliderLayout.setSpacing(0)
        sliderLayout.addWidget(self.prev3Slider, 0, 0)
        sliderLayout.addWidget(self.prev3Check, 1, 0)
        sliderLayout.addWidget(self.prev2Slider, 0, 1)
        sliderLayout.addWidget(self.prev2Check, 1, 1)
        sliderLayout.addWidget(self.prev1Slider, 0, 2)
        sliderLayout.addWidget(self.prev1Check, 1, 2)
        sliderLayout.addWidget(self.currentSlider, 0, 3)
        sliderLayout.addWidget(self.next1Slider, 0, 4)
        sliderLayout.addWidget(self.next1Check, 1, 4)
        sliderLayout.addWidget(self.next2Slider, 0, 5)
        sliderLayout.addWidget(self.next2Check, 1, 5)
        sliderLayout.addWidget(self.next3Slider, 0, 6)
        sliderLayout.addWidget(self.next3Check, 1, 6)
        layout = QtGui.QVBoxLayout()
        layout.addLayout(colorLayout)
        layout.addLayout(sliderLayout)
        self.setLayout(layout)
        
    def valueChanged(self, value):
        self.project.onionSkin["prev"] = [[self.prev1Check.isChecked(), self.prev1Slider.value()/100],
                                          [self.prev2Check.isChecked(), self.prev2Slider.value()/100],
                                          [self.prev3Check.isChecked(), self.prev3Slider.value()/100]]
        self.project.onionSkin["next"] = [[self.next1Check.isChecked(), self.next1Slider.value()/100],
                                          [self.next2Check.isChecked(), self.next2Slider.value()/100],
                                          [self.next3Check.isChecked(), self.next3Slider.value()/100]]
        self.project.updateViewSign.emit()
        
    def checkColor(self):
        self.project.onionSkin["color"] = self.colorCheck.isChecked()
        self.project.updateViewSign.emit()

    def prevColorChanged(self):
        ok, color = ColorDialog(False, self.project.onionSkin["prev_color"]).getQColor()
        if not ok:
            return
        self.project.onionSkin["prev_color"] = color
        self.prevcolorIcon.fill(self.project.onionSkin["prev_color"])
        self.colorPrevB.setIcon(QtGui.QIcon(self.prevcolorIcon))
        self.project.updateViewSign.emit()
        
    def nextColorChanged(self):
        ok, color = ColorDialog(False, self.project.onionSkin["next_color"]).getQColor()
        if not ok:
            return
        self.project.onionSkin["next_color"] = color
        self.nextcolorIcon.fill(self.project.onionSkin["next_color"])
        self.colorNextB.setIcon(QtGui.QIcon(self.nextcolorIcon))
        self.project.updateViewSign.emit()
