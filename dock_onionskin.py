#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from PyQt4 import QtCore
from PyQt4 import QtGui

from widget import Button
from colorPicker import ColorDialog
"""
        self.onionSkin = {"check"     : False,
                          "color"     : False,
                          "prevColor" : None,
                          "prev"      : [[True, 0.5], [True, 0.5], [True, 0.5]],
                          "nextColor" : None,
                          "next"      : [[True, 0.5], [True, 0.5], [True, 0.5]]}
"""
class OnionSkinWidget(QtGui.QWidget):
    def __init__(self, project):
        QtGui.QWidget.__init__(self)
        self.project = project
        
        self.prevColor = QtGui.QColor(255, 0, 0)
        self.prevcolorIcon = QtGui.QPixmap(32, 16)
        self.prevcolorIcon.fill(self.prevColor)
        self.colorPrevB = Button("previous frames color",
            QtGui.QIcon(self.prevcolorIcon), self.prevColorChanged)
        self.colorPrevB.setIconSize(QtCore.QSize(36, 20))
        self.colorPrevB.setDisabled(True)
        
        self.colorCheck = QtGui.QCheckBox(self)
        self.colorCheck.setToolTip("colored onion skin")
        self.colorCheck.setDisabled(True)
        
        self.nextColor = QtGui.QColor(0, 0, 255)
        self.nextcolorIcon = QtGui.QPixmap(32, 16)
        self.nextcolorIcon.fill(self.nextColor)
        self.colorNextB = Button("next frames color",
            QtGui.QIcon(self.nextcolorIcon), self.nextColorChanged)
        self.colorNextB.setIconSize(QtCore.QSize(36, 20))
        self.colorNextB.setDisabled(True)
        
        
        self.prev1Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.prev1Slider.setRange(0, 100)
        self.prev1Slider.setValue(50)
        self.prev1Slider.valueChanged.connect(self.valueChanged)
        self.prev1Check = QtGui.QCheckBox(self)
        self.prev1Check.setChecked(True)
        self.prev1Check.stateChanged.connect(self.valueChanged)
        self.prev2Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.prev2Slider.setRange(0, 100)
        self.prev2Slider.setValue(25)
        self.prev2Slider.valueChanged.connect(self.valueChanged)
        self.prev2Check = QtGui.QCheckBox(self)
        self.prev2Check.stateChanged.connect(self.valueChanged)
        self.prev3Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.prev3Slider.setRange(0, 100)
        self.prev3Slider.setValue(12)
        self.prev3Slider.valueChanged.connect(self.valueChanged)
        self.prev3Check = QtGui.QCheckBox(self)
        self.prev3Check.stateChanged.connect(self.valueChanged)
        
        self.currentSlider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.currentSlider.setRange(0, 100)
        self.currentSlider.setValue(100)
        self.currentSlider.setDisabled(True)
        self.currentSlider.setMinimumHeight(100)
        
        self.next1Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.next1Slider.setRange(0, 100)
        self.next1Slider.setValue(50)
        self.next1Slider.valueChanged.connect(self.valueChanged)
        self.next1Check = QtGui.QCheckBox(self)
        self.next1Check.setChecked(True)
        self.next1Check.stateChanged.connect(self.valueChanged)
        self.next2Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.next2Slider.setRange(0, 100)
        self.next2Slider.setValue(25)
        self.next2Slider.valueChanged.connect(self.valueChanged)
        self.next2Check = QtGui.QCheckBox(self)
        self.next2Check.stateChanged.connect(self.valueChanged)
        self.next3Slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.next3Slider.setRange(0, 100)
        self.next3Slider.setValue(12)
        self.next3Slider.valueChanged.connect(self.valueChanged)
        self.next3Check = QtGui.QCheckBox(self)
        self.next3Check.stateChanged.connect(self.valueChanged)
        
        self.valueChanged(None)
        
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
        self.project.onionSkin["prev"] = [[self.prev1Check.isChecked(), self.prev1Slider.value()],
                                          [self.prev2Check.isChecked(), self.prev2Slider.value()],
                                          [self.prev3Check.isChecked(), self.prev3Slider.value()]]
        self.project.onionSkin["next"] = [[self.next1Check.isChecked(), self.next1Slider.value()],
                                          [self.next2Check.isChecked(), self.next2Slider.value()],
                                          [self.next3Check.isChecked(), self.next3Slider.value()]]
        self.project.updateViewSign.emit()
        
    def checkColor(self):
        pass

    def prevColorChanged(self):
        ok, color = ColorDialog(False, self.prevColor).getQColor()
        if not ok:
            return
        self.prevColor = color
        self.prevcolorIcon.fill(self.prevColor)
        self.colorPrevB.setIcon(QtGui.QIcon(self.prevcolorIcon))
        
    def nextColorChanged(self):
        ok, color = ColorDialog(False, self.nextColor).getQColor()
        if not ok:
            return
        self.nextColor = color
        self.nextcolorIcon.fill(self.nextColor)
        self.colorNextB.setIcon(QtGui.QIcon(self.nextcolorIcon))
