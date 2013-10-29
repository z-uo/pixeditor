#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Python 3 Compatibility
from __future__ import division
from __future__ import print_function

import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt
from colorPicker import ColorDialog
from widget import Background
from import_export import import_palette


class BackgroundDialog(QtGui.QDialog):
    def __init__(self, color=QtGui.QColor(150, 150, 150), arg=16):
        """ color: QColor is the background color
            arg can be
                int: square pattern, arg is the size
                str: custom pattern, arg is the filename
        """
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("background")
        ### color ###
        self.color = color
        self.colorL = QtGui.QLabel("color :")
        self.colorIcon = QtGui.QPixmap(40, 20)
        self.colorIcon.fill(self.color)
        self.colorW = QtGui.QToolButton(self)
        self.colorW.setAutoRaise(True)
        self.colorW.setIcon(QtGui.QIcon(self.colorIcon))
        self.colorW.setIconSize(QtCore.QSize(46, 26))
        ### preview ###
        self.preview = QtGui.QPixmap(128, 128)
        self.preview.fill(self.color)
        self.previewL = QtGui.QLabel()
        self.previewL.setPixmap(self.preview)
        
        ### square pattern ###
        self.squareRadio = QtGui.QRadioButton("square", self)
        self.sizeL = QtGui.QLabel("size :")
        self.sizeW = QtGui.QLineEdit("16", self)
        self.sizeW.setValidator(QtGui.QIntValidator(self.sizeW))
        
        ### file pattern ###
        self.fileRadio = QtGui.QRadioButton("file", self)
        ### model to store images ###
        self.modImgList = QtGui.QStandardItemModel(0, 1)
        for f in os.listdir(os.path.join("resources", "pattern")):
            if f.endswith(".png"):
                i = QtGui.QStandardItem(f)
                i.path = os.path.join("resources", "pattern", f)
                self.modImgList.appendRow(i)

        ### listview to display images ###
        self.imgList = QtGui.QListView()
        self.imgList.setModel(self.modImgList)
        self.imgList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        # select the first one
        self.fileName = self.modImgList.item(0).path
        sel = self.modImgList.createIndex(0, 0)
        self.imgList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)
        
        ### init ###
        if type(arg) is int:
            self.pattern = "square"
            self.squareRadio.setChecked(True)
            self.size = arg
            self.sizeW.setText(str(self.size))
        elif type(arg) is str:
            self.pattern = "file"
            self.fileRadio.setChecked(True)
            for i in range(self.modImgList.rowCount()):
                if arg == self.modImgList.item(i).path:
                    self.imgList.selectionModel().clear()
                    sel = self.modImgList.createIndex(i, 0)
                    self.imgList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)
                    self.fileName = arg
            self.size = 16
            
        ### preview ###
        self.updatePreview()
        # connect
        self.colorW.clicked.connect(self.colorClicked)
        self.squareRadio.toggled.connect(self.radioToggled)
        self.sizeW.textChanged.connect(self.sizeChanged)
        self.imgList.selectionModel().selectionChanged.connect(self.fileChanged)
        
        ### apply, undo ###
        self.cancelW = QtGui.QPushButton('cancel', self)
        self.cancelW.clicked.connect(self.cancelClicked)
        self.okW = QtGui.QPushButton('ok', self)
        self.okW.clicked.connect(self.okClicked)
        self.okW.setDefault(True)

        grid = QtGui.QGridLayout()
        grid.setSpacing(4)
        grid.addWidget(self.colorL, 0, 1)
        grid.addWidget(self.colorW, 0, 2)
        
        grid.addWidget(self.squareRadio, 1, 0)
        grid.addWidget(self.sizeL, 1, 1)
        grid.addWidget(self.sizeW, 1, 2)
        
        grid.addWidget(self.fileRadio, 2, 0)
        grid.addWidget(self.imgList, 2, 1, 2, 2)
        
        grid.addWidget(self.previewL, 0, 3, 4, 1)

        okBox = QtGui.QHBoxLayout()
        okBox.addStretch(0)
        okBox.addWidget(self.cancelW)
        okBox.addWidget(self.okW)

        vBox = QtGui.QVBoxLayout()
        vBox.addLayout(grid)
        vBox.addStretch(0)
        vBox.addLayout(okBox)

        self.setLayout(vBox)
        self.exec_()
        
    def colorClicked(self):
        ok, color = ColorDialog(False, self.color).getQColor()
        if ok:
            self.color = color
            self.colorIcon.fill(self.color)
            self.colorW.setIcon(QtGui.QIcon(self.colorIcon))
            self.updatePreview()
        
    def sizeChanged(self, s):
        try:
            self.size = int(s)
        except ValueError:
            self.size = 0
        if self.pattern == "square":
            self.updatePreview()
        
    def radioToggled(self):
        if self.squareRadio.isChecked():
            self.pattern = "square"
        elif self.fileRadio.isChecked():
            self.pattern = "file"
        self.updatePreview()
            
    def fileChanged(self):
        sel = self.imgList.selectionModel().selectedIndexes()[0].row()
        self.fileName = self.modImgList.item(sel).path
        if self.pattern == "file":
            self.updatePreview()
        
    def updatePreview(self):
        self.preview.fill(self.color)
        p = QtGui.QPainter(self.preview)
        if self.pattern == "square":
            p.drawPixmap(16, 16, Background(QtCore.QSize(96, 96), self.size))
        elif self.pattern == "file":
            p.drawPixmap(16, 16, Background(QtCore.QSize(96, 96), self.fileName))
        self.previewL.setPixmap(self.preview)
        
    def okClicked(self):
        try:
            self.size = int(self.sizeW.text())
        except ValueError:
            self.size = 0
        self.accept()

    def cancelClicked(self):
        self.reject()

    def getReturn(self):
        if self.result():
            if self.pattern == "square":
                return self.color, self.size
            elif self.pattern == "file":
                return self.color, self.fileName
        return None, None

class NewDialog(QtGui.QDialog):
    def __init__(self, size=QtCore.QSize(64, 64)):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("new animation")

        ### instructions ###
        self.instL = QtGui.QLabel("Enter the size of the new animation :")
        ### width ###
        self.wL = QtGui.QLabel("width")
        self.wW = QtGui.QLineEdit(str(size.width()), self)
        self.wW.setValidator(QtGui.QIntValidator(self.wW))
        ### height ###
        self.hL = QtGui.QLabel("height")
        self.hW = QtGui.QLineEdit(str(size.height()), self)
        self.hW.setValidator(QtGui.QIntValidator(self.hW))
        ### error ###
        self.errorL = QtGui.QLabel("")
        
        ### palette ###
        palettePath = os.path.join("resources", "palette")
        ls = os.listdir(palettePath)
        ls.sort()
        self.paletteDict = {}
            
        self.paletteW = QtGui.QComboBox(self)
        for i in ls:
            self.paletteDict[os.path.splitext(i)[0]] = os.path.join(palettePath, i)
            self.paletteW.addItem(os.path.splitext(i)[0])
            
        ### apply, undo ###
        self.cancelW = QtGui.QPushButton('cancel', self)
        self.cancelW.clicked.connect(self.cancelClicked)
        self.newW = QtGui.QPushButton('new', self)
        self.newW.clicked.connect(self.newClicked)
        self.newW.setDefault(True)

        grid = QtGui.QGridLayout()
        grid.setSpacing(4)
        grid.addWidget(self.instL, 0, 0, 1, 2)
        grid.addWidget(self.wL, 1, 0)
        grid.addWidget(self.hL, 2, 0)
        grid.addWidget(self.wW, 1, 1)
        grid.addWidget(self.hW, 2, 1)
        grid.addWidget(self.errorL, 3, 0, 1, 2)
        grid.addWidget(self.paletteW, 4, 0, 1, 2)

        okBox = QtGui.QHBoxLayout()
        okBox.addStretch(0)
        okBox.addWidget(self.cancelW)
        okBox.addWidget(self.newW)

        vBox = QtGui.QVBoxLayout()
        vBox.addLayout(grid)
        vBox.addStretch(0)
        vBox.addLayout(okBox)

        self.setLayout(vBox)
        self.exec_()
    def get_palette_list(self):
        pass
    def newClicked(self):
        try:
            self.size = QtCore.QSize(int(self.wW.text()), int(self.hW.text()))
        except ValueError:
            self.errorL.setText("ERROR : You must enter a number !")
            return
        self.palette = import_palette(self.paletteDict[self.paletteW.currentText()])
        if self.size.isEmpty():
            self.errorL.setText("ERROR : The size must be greater than 0 !")
        else:
            self.accept()

    def cancelClicked(self):
        self.reject()

    def getReturn(self):
        if self.result():
            return self.size, self.palette

class CropDialog(QtGui.QDialog):
    def __init__(self, size):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("crop animation")

        ### instructions ###
        self.wL = QtGui.QLabel("width")
        self.wL.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.hL = QtGui.QLabel("height")
        self.hL.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.actualSizeL = QtGui.QLabel("Actual size")
        self.actualSizeL.setAlignment(QtCore.Qt.AlignCenter)
        self.actualWL = QtGui.QLabel(str(size.width()))
        self.actualHL = QtGui.QLabel(str(size.height()))
        self.newSizeL = QtGui.QLabel("New size")
        self.newSizeL.setAlignment(QtCore.Qt.AlignCenter)
        self.newWW = QtGui.QLineEdit(str(size.width()), self)
        self.newWW.setValidator(QtGui.QIntValidator(self.newWW))
        self.newHW = QtGui.QLineEdit(str(size.height()), self)
        self.newHW.setValidator(QtGui.QIntValidator(self.newHW))
        ### offset ###
        self.offsetL = QtGui.QLabel("offset")
        self.offsetL.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalL = QtGui.QLabel("horizontal")
        self.horizontalL.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.horizontalOffsetW = QtGui.QLineEdit(str(0), self)
        self.horizontalOffsetW.setValidator(QtGui.QIntValidator(self.horizontalOffsetW))
        self.verticalL = QtGui.QLabel("vertical")
        self.verticalL.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.verticalOffsetW = QtGui.QLineEdit(str(0), self)
        self.verticalOffsetW.setValidator(QtGui.QIntValidator(self.verticalOffsetW))

        ### error ###
        self.errorL = QtGui.QLabel("")
        ### apply, undo ###
        self.cancelW = QtGui.QPushButton('cancel', self)
        self.cancelW.clicked.connect(self.cancelClicked)
        self.cropW = QtGui.QPushButton('crop', self)
        self.cropW.clicked.connect(self.cropClicked)
        self.cropW.setDefault(True)

        grid = QtGui.QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(self.wL, 1, 0)
        grid.addWidget(self.hL, 2, 0)

        grid.addWidget(self.actualSizeL, 0, 1)
        grid.addWidget(self.actualWL, 1, 1)
        grid.addWidget(self.actualHL, 2, 1)

        grid.addWidget(self.newSizeL, 0, 2)
        grid.addWidget(self.newWW, 1, 2)
        grid.addWidget(self.newHW, 2, 2)

        grid.addWidget(self.offsetL, 3, 2)

        grid.addWidget(self.horizontalL, 4, 1)
        grid.addWidget(self.verticalL, 5, 1)
        grid.addWidget(self.horizontalOffsetW, 4, 2)
        grid.addWidget(self.verticalOffsetW, 5, 2)

        grid.addWidget(self.errorL, 6, 0, 1, 3)

        okBox = QtGui.QHBoxLayout()
        okBox.addStretch(0)
        okBox.addWidget(self.cancelW)
        okBox.addWidget(self.cropW)

        vBox = QtGui.QVBoxLayout()
        vBox.addLayout(grid)
        vBox.addStretch(0)
        vBox.addLayout(okBox)

        self.setLayout(vBox)
        self.exec_()

    def cropClicked(self):
        try:
            w = int(self.newWW.text())
            h = int(self.newHW.text())
        except ValueError:
            self.errorL.setText("ERROR : You must enter a number !")
            return
        try:
            wOffset = int(self.horizontalOffsetW.text())
        except ValueError:
            wOffset = 0
        try:
            hOffset = int(self.verticalOffsetW.text())
        except ValueError:
            hOffset = 0
        if w > 0 and h > 0:
            self.rect = QtCore.QRect(wOffset, hOffset, w, h) 
            self.accept()
        else:
            self.errorL.setText("ERROR : The size must be greater than 0 !")

    def cancelClicked(self):
        self.reject()

    def getReturn(self):
        if self.result():
            return self.rect

class ResizeDialog(QtGui.QDialog):
    def __init__(self, size):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("resize animation")
        self.w, self.h = size.width(), size.height()
        
        self.factor = 1
        self.factorW = QtGui.QComboBox(self)
        self.factorW.addItems(["0.25","0.5","1","2","4"])
        self.factorW.setCurrentIndex(2)
        self.factorW.activated[str].connect(self.factorClicked)
        
        ### instructions ###
        self.wL = QtGui.QLabel("width")
        self.wL.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.hL = QtGui.QLabel("height")
        self.hL.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.actualSizeL = QtGui.QLabel("Actual size")
        self.actualSizeL.setAlignment(QtCore.Qt.AlignCenter)
        self.actualWL = QtGui.QLabel(str(self.w))
        self.actualHL = QtGui.QLabel(str(self.h))
        self.newSizeL = QtGui.QLabel("New size")
        self.newSizeL.setAlignment(QtCore.Qt.AlignCenter)
        self.newWL = QtGui.QLabel(str(self.w))
        self.newHL = QtGui.QLabel(str(self.h))

        ### apply, undo ###
        self.cancelW = QtGui.QPushButton('cancel', self)
        self.cancelW.clicked.connect(self.cancelClicked)
        self.resizeW = QtGui.QPushButton('resize', self)
        self.resizeW.clicked.connect(self.resizeClicked)
        self.resizeW.setDefault(True)

        grid = QtGui.QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(self.factorW, 0, 1, 1, 2)
        grid.addWidget(self.wL, 1, 1)
        grid.addWidget(self.hL, 1, 2)

        grid.addWidget(self.actualSizeL, 2, 0)
        grid.addWidget(self.actualWL, 2, 1)
        grid.addWidget(self.actualHL, 2, 2)

        grid.addWidget(self.newSizeL, 3, 0)
        grid.addWidget(self.newWL, 3, 1)
        grid.addWidget(self.newHL, 3, 2)

        okBox = QtGui.QHBoxLayout()
        okBox.addStretch(0)
        okBox.addWidget(self.cancelW)
        okBox.addWidget(self.resizeW)

        vBox = QtGui.QVBoxLayout()
        vBox.addLayout(grid)
        vBox.addStretch(0)
        vBox.addLayout(okBox)

        self.setLayout(vBox)
        self.exec_()
        
    def factorClicked(self, n):
        self.factor = float(n)
        self.newWL.setText(str(int(self.w * self.factor)))
        self.newHL.setText(str(int(self.h * self.factor)))
        
    def resizeClicked(self):
        self.accept()

    def cancelClicked(self):
        self.reject()

    def getReturn(self):
        if self.result():
            return self.factor

class RenameLayerDialog(QtGui.QDialog):
    def __init__(self, name):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("rename layer")

        self.name = name
        ### instructions ###
        self.instL = QtGui.QLabel("Enter the new name of the layer :")
        self.nameW = QtGui.QLineEdit(name, self)
        ### error ###
        self.errorL = QtGui.QLabel("")
        ### apply, undo ###
        self.cancelW = QtGui.QPushButton('cancel', self)
        self.cancelW.clicked.connect(self.cancelClicked)
        self.renameW = QtGui.QPushButton('rename', self)
        self.renameW.clicked.connect(self.renameClicked)
        self.renameW.setDefault(True)
        okBox = QtGui.QHBoxLayout()
        okBox.addStretch(0)
        okBox.addWidget(self.cancelW)
        okBox.addWidget(self.renameW)

        vBox = QtGui.QVBoxLayout()
        vBox.addWidget(self.instL)
        vBox.addWidget(self.nameW)
        vBox.addWidget(self.errorL)
        vBox.addLayout(okBox)

        self.setLayout(vBox)
        self.exec_()

    def renameClicked(self):
        n = self.nameW.text()
        if n == self.name:
            self.reject()
        else:
            self.name = n
            self.accept()

    def cancelClicked(self):
        self.reject()

    def getReturn(self):
        if self.result():
            return self.name

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    #~ mainWin = RenameLayerDialog("layer 1")
    #~ mainWin = ResizeDialog((24, 32))
    #~ mainWin = BackgroundDialog(QtGui.QColor(150, 150, 150), "pattern/iso_20x11.png")
    mainWin = BackgroundDialog()
    sys.exit(app.exec_())
