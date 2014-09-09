#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Copyright Nicolas Bougère (nicolas.bougere@z-uo.com), 2012-2014
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui

from data import Project
from dock_timeline import TimelineWidget
from dock_tools import ToolsWidget
from dock_palette import PaletteWidget
from dock_options import OptionsWidget
from dock_onionskin import OnionSkinWidget
from dialogs import *
from widget import Dock
from import_export import *
from widget import Background

class SelectionRect(QtGui.QGraphicsRectItem):
    """ Rect item used in scene to display a selection """
    def __init__(self, pos):
        QtGui.QGraphicsRectItem.__init__(self, pos.x(), pos.y(), 1, 1)
        self.startX = pos.x()
        self.startY = pos.y()
        
        self.setPen(QtGui.QPen(QtGui.QColor("black"), 0))
        dashPen = QtGui.QPen(QtGui.QColor("white"), 0, QtCore.Qt.DashLine)
        dashPen.setDashPattern([6, 6])
        self.dash = QtGui.QGraphicsRectItem(self.rect(), self)
        self.dash.setPen(dashPen)
        
    def scale(self, pos):
        rect = QtCore.QRectF(self.startX, self.startY, pos.x() - self.startX, pos.y() - self.startY)
        self.setRect(rect)
        self.dash.setRect(rect)
        
    def getRect(self):
        """ return a QRect with positive width and height """
        w = int(self.rect().width())
        h = int(self.rect().height())
        if w < 0:
            x = int(self.rect().x()) + w
            w = int(self.rect().x()) - x
        else:
            x = int(self.rect().x())
        if h < 0:
            y = int(self.rect().y()) + h
            h = int(self.rect().y()) - y
        else:
            y = int(self.rect().y())
        return QtCore.QRect(x, y, w, h)
        
        
class Scene(QtGui.QGraphicsView):
    """ widget used to display the layers, onionskin, pen, background
        it can zoom with mouseWheel, pan with mouseMiddleClic
        it send mouseRightClic info to the current Canvas"""
    def __init__(self, project):
        QtGui.QGraphicsView.__init__(self)
        self.project = project
        self.zoomN = 1
        self.setAcceptDrops(False)
        # scene
        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.setScene(self.scene)
        self.setTransformationAnchor(
                QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.setMinimumSize(400, 400)
        self.scene.setSceneRect(0, 0, 
                    self.project.size.width(), self.project.size.height())
        # coords info
        self.coords=None
        # background
        self.setBackgroundBrush(QtGui.QBrush(self.project.bgColor))
        self.bg = self.scene.addPixmap(
                    Background(self.project.size, self.project.bgPattern))
        # frames
        self.itemList = []
        self.canvasList = []
        # OnionSkin
        self.onionPrevItems = []
        for i in range(3):
            p = QtGui.QPixmap(self.project.size)
            self.onionPrevItems.append(self.scene.addPixmap(p))
            self.onionPrevItems[-1].setZValue(101+i)
            self.onionPrevItems[-1].hide()
        self.onionNextItems = []
        for i in range(3):
            p = QtGui.QPixmap(self.project.size)
            self.onionNextItems.append(self.scene.addPixmap(p))
            self.onionNextItems[-1].setZValue(104+i)
            self.onionNextItems[-1].hide()
        
        # pen
        self.penItem = QtGui.QGraphicsRectItem(0, 0, 1, 1)
        self.penItem.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 0)))
        self.penItem.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.scene.addItem(self.penItem)
        self.penItem.setZValue(120)
        self.penItem.hide()
        self.project.penChangedSign.connect(self.changePen)
        self.project.toolChangedSign.connect(self.changePen)
        self.project.colorChangedSign.connect(self.changePen)
        self.changePen()

        self.project.updateViewSign.connect(self.changeFrame)
        self.project.updateBackgroundSign.connect(self.updateBackground)
        self.changeFrame()

    def changePen(self):
        for i in self.penItem.childItems():
            self.scene.removeItem(i)
        if self.project.tool == "pen" and self.project.pen:
            pen = QtGui.QPen(QtCore.Qt.NoPen)
            if len(self.project.pen[0]) == 3:
                for i in self.project.pen:
                    brush = QtGui.QColor(self.project.colorTable[i[2]])
                    p = QtGui.QGraphicsRectItem(i[0], i[1], 1, 1, self.penItem)
                    p.setPen(pen)
                    p.setBrush(brush)
            else:
                brush = QtGui.QColor(self.project.colorTable[self.project.color])
                for i in self.project.pen:
                    p = QtGui.QGraphicsRectItem(i[0], i[1], 1, 1, self.penItem)
                    p.setPen(pen)
                    p.setBrush(brush)
                
    def updateBackground(self):
        self.setBackgroundBrush(QtGui.QBrush(self.project.bgColor))
        self.bg.setPixmap(Background(self.project.size, 
                                     self.project.bgPattern))
        
    def changeFrame(self):
        self.canvasList = self.project.timeline.getCanvasList(self.project.curFrame)
        # resize scene if needed
        if self.scene.sceneRect().size().toSize() != self.project.size:
            self.scene.setSceneRect(0, 0, 
                    self.project.size.width(), self.project.size.height())
            self.updateBackground()
        # add item for layer if needed
        for i in range(len(self.itemList), len(self.canvasList)):
            self.itemList.append(self.scene.addPixmap(QtGui.QPixmap(1, 1)))
            self.itemList[i].setZValue(100 - i)
        # remove item for layer if needed
        for i in range(len(self.canvasList), len(self.itemList)):
            self.scene.removeItem(self.itemList[i])
            del self.itemList[i]
        # updates canvas
        for n, i in enumerate(self.canvasList):
            if i and self.project.timeline[n].visible:
                self.itemList[n].setVisible(True)
                self.itemList[n].pixmap().convertFromImage(i)
                self.itemList[n].update()
                self.itemList[n].setOpacity(self.project.currentOpacity)
            else:
                self.itemList[n].setVisible(False)
        # onionskin
        for i in self.onionPrevItems:
            i.hide()
        for i in self.onionNextItems:
            i.hide()
        layer = self.project.timeline[self.project.curLayer]
        if (not self.project.playing and self.project.onionSkin["check"] and 
             layer.visible and self.project.curFrame < len(layer)):
            # previous frames
            for n, i in enumerate(layer.getPrevCanvas(3)):
                if self.project.onionSkin["prev"][n][0]:
                    self.onionPrevItems[n].pixmap().convertFromImage(i)
                    if self.project.onionSkin["color"]:
                        prevEffect = QtGui.QGraphicsColorizeEffect()
                        prevEffect.setColor(self.project.onionSkin["prev_color"])
                        self.onionPrevItems[n].setGraphicsEffect(prevEffect)
                    else:
                        self.onionPrevItems[n].setGraphicsEffect(None)
                    self.onionPrevItems[n].setOpacity(self.project.onionSkin["prev"][n][1])
                    self.onionPrevItems[n].show()
            # next frames
            for n, i in enumerate(layer.getNextCanvas(3)):
                if self.project.onionSkin["next"][n][0]:
                    self.onionNextItems[n].pixmap().convertFromImage(i)
                    if self.project.onionSkin["color"]:
                        nextEffect = QtGui.QGraphicsColorizeEffect()
                        nextEffect.setColor(self.project.onionSkin["next_color"])
                        self.onionNextItems[n].setGraphicsEffect(nextEffect)
                    else:
                        self.onionNextItems[n].setGraphicsEffect(None)
                    self.onionNextItems[n].setOpacity(self.project.onionSkin["next"][n][1])
                    self.onionNextItems[n].show()

    def wheelEvent(self, event):
        if event.delta() > 0:
            self.scaleView(2)
        elif event.delta() < 0:
            self.scaleView(0.5)

    def scaleView(self, factor):
        n = self.zoomN * factor
        if n < 1 or n > 32:
            return
        self.zoomN = n
        self.penItem.hide()
        self.scale(factor, factor)

    def pointToInt(self, point):
        return QtCore.QPoint(int(point.x()), int(point.y()))

    def pointToFloat(self, point):
        return QtCore.QPointF(int(point.x()), int(point.y()))

    def mousePressEvent(self, event):
        l = self.project.curLayer
        # pan
        if event.buttons() == QtCore.Qt.MidButton:
            self.startScroll = (self.horizontalScrollBar().value(),
                                self.verticalScrollBar().value())
            self.lastPos = QtCore.QPoint(QtGui.QCursor.pos())
            self.setDragMode(QtGui.QGraphicsView.NoDrag)
        # draw on canvas
        elif (self.project.timeline[l].visible
                and (event.buttons() == QtCore.Qt.LeftButton 
                    or event.buttons() == QtCore.Qt.RightButton)
                and self.project.tool == "pen" 
                or self.project.tool == "pipette" 
                or self.project.tool == "fill"):
            pos = self.pointToInt(self.mapToScene(event.pos()))
            if not self.canvasList[l] and self.project.tool == "pen" :
                self.project.timeline[self.project.curLayer].insertCanvas(
                        self.project.curFrame, self.project.makeCanvas())
                self.project.updateTimelineSign.emit()
                self.project.updateViewSign.emit()
            self.canvasList[l].clic(pos, event.buttons())
            self.itemList[l].pixmap().convertFromImage(self.canvasList[l])
            self.itemList[l].update()
        # move or select
        elif (self.project.timeline[l].visible and self.canvasList[l]
                and event.buttons() == QtCore.Qt.LeftButton):
            pos = self.pointToInt(self.mapToScene(event.pos()))
            if self.project.tool == "move":
                self.lastPos = pos
            elif self.project.tool == "select":
                self.selRect = SelectionRect(pos)
                self.selRect.setZValue(103)
                self.scene.addItem(self.selRect)
        else:
            return QtGui.QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        self.penItem.show()
        self.penItem.setPos(self.pointToFloat(self.mapToScene(event.pos())))
        # show cursor coordinates
        pos = self.pointToInt(self.mapToScene(event.pos()))
        if (pos.x()>=0 and pos.y()>=0 \
          and pos.x()<self.project.size.width() \
          and pos.y()<self.project.size.height()):
          self.coords.setText("x %(x)03d\ny %(y)03d"%{"x":pos.x(),"y":pos.y()});
        else:
          self.coords.setText("x\ny");
        
        l = self.project.curLayer
        # pan
        if event.buttons() == QtCore.Qt.MidButton:
            globalPos = QtGui.QCursor.pos()
            self.horizontalScrollBar().setValue(self.startScroll[0] -
                    globalPos.x() + self.lastPos.x())
            self.verticalScrollBar().setValue(self.startScroll[1] -
                    globalPos.y() + self.lastPos.y())
        # draw on canvas
        elif (self.project.timeline[l].visible and self.canvasList[l] 
                and (event.buttons() == QtCore.Qt.LeftButton 
                    or event.buttons() == QtCore.Qt.RightButton)
                and self.project.tool == "pen"
                or self.project.tool == "pipette" 
                or self.project.tool == "fill"):
            pos = self.pointToInt(self.mapToScene(event.pos()))
            self.canvasList[l].move(pos, event.buttons())
            self.itemList[l].pixmap().convertFromImage(self.canvasList[l])
            self.itemList[l].update()
        # move or select
        elif (self.project.timeline[l].visible and self.canvasList[l]
                and event.buttons() == QtCore.Qt.LeftButton):
            pos = self.pointToInt(self.mapToScene(event.pos()))
            if self.project.tool == "move":
                dif = pos - self.lastPos
                intPos = self.pointToInt(self.itemList[l].pos())
                self.itemList[l].setPos(QtCore.QPointF(intPos + dif))
                self.lastPos = pos
            elif self.project.tool == "select": 
                self.selRect.scale(pos)
        else:
            return QtGui.QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            l = self.project.curLayer
            if self.project.tool == "move" and self.canvasList[l] and self.itemList[l].pos():
                self.project.saveToUndo("canvas")
                offset = (int(self.itemList[l].pos().x()), 
                          int(self.itemList[l].pos().y()))
                self.canvasList[l].loadFromList(
                                    self.canvasList[l].returnAsList(),
                                    None, offset, self.project.moveMode)
                self.itemList[l].setPos(QtCore.QPointF(0, 0))
                self.changeFrame()
            elif self.project.tool == "select": 
                rect = self.selRect.getRect()
                if rect.isValid():
                    sel = self.canvasList[l].returnAsMatrix(rect)
                    if self.project.selectMode == "cut":
                        self.project.saveToUndo("canvas")
                        self.canvasList[l].delRect(rect)
                    self.project.customPenSign.emit(sel)
                    self.changeFrame()
                self.scene.removeItem(self.selRect)
                del self.selRect
        else:
            return QtGui.QGraphicsView.mouseReleaseEvent(self, event)

    def enterEvent(self, event):
        self.penItem.show()

    def leaveEvent(self, event):
        self.penItem.hide()
        

class MainWindow(QtGui.QMainWindow):
    """ Main windows of the application """
    dropped = QtCore.pyqtSignal(list)
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setAcceptDrops(True)
        self.dropped.connect(self.importAsLayer)
        
        self.project = Project(self)
        self.toolsWidget = ToolsWidget(self.project)
        self.optionsWidget = OptionsWidget(self.project)
        self.paletteWidget = PaletteWidget(self.project)
        self.onionSkinWidget = OnionSkinWidget(self.project)
        self.timelineWidget = TimelineWidget(self.project)
        self.scene = Scene(self.project)
        
        self.updateTitle()
        self.project.updateTitleSign.connect(self.updateTitle)

        ### layout #####################################################
        self.setDockNestingEnabled(True)
        self.setCentralWidget(self.scene)
        
        QtGui.QApplication.setOrganizationName("pixeditor")
        QtGui.QApplication.setApplicationName("pixeditor")
        settings = QtCore.QSettings()
        settings.beginGroup("mainWindow")
        try:
            lock = bool(int(settings.value("lock")))
        except TypeError:
            lock = True
        
        toolsDock = Dock(self.toolsWidget, "tools", lock)
        toolsDock.setObjectName("toolsDock")
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, toolsDock)
        self.scene.coords=toolsDock.widget().coords

        optionsDock = Dock(self.optionsWidget, "options", lock)
        optionsDock.setObjectName("optionsDock")
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, optionsDock)

        paletteDock = Dock(self.paletteWidget, "palette", lock)
        paletteDock.setObjectName("paletteDock")
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, paletteDock)
        
        onionSkinDock = Dock(self.onionSkinWidget, "onion skin", lock)
        onionSkinDock.setObjectName("onionSkinDock")
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, onionSkinDock)
        
        timelineDock = Dock(self.timelineWidget, "timeline", lock)
        timelineDock.setObjectName("timelineDock")
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, timelineDock)

        ### File menu ###
        menubar = self.menuBar()
        openAction = QtGui.QAction('Open', self)
        openAction.triggered.connect(self.openAction)
        saveAsAction = QtGui.QAction('Save as', self)
        saveAsAction.triggered.connect(self.saveAsAction)
        saveAction = QtGui.QAction('Save', self)
        saveAction.triggered.connect(self.saveAction)
        saveAction.setShortcut('Ctrl+S')
        
        importNewAction = QtGui.QAction('Import as new', self)
        importNewAction.triggered.connect(self.importAsNewAction)
        importLayerAction = QtGui.QAction('Import as layer', self)
        importLayerAction.triggered.connect(self.importAsLayerAction)
        exportAction = QtGui.QAction('Export', self)
        exportAction.triggered.connect(self.exportAction)
        exportAction.setShortcut('Ctrl+E')
        
        exitAction = QtGui.QAction('Exit', self)
        exitAction.triggered.connect(self.close)
        exitAction.setShortcut('Ctrl+Q')
        
        fileMenu = menubar.addMenu('File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(saveAction)
        fileMenu.addSeparator()
        fileMenu.addAction(importNewAction)
        fileMenu.addAction(importLayerAction)
        fileMenu.addAction(exportAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)
        
        ### Edit menu ###
        undoAction = QtGui.QAction('Undo', self)
        undoAction.triggered.connect(self.project.undo)
        undoAction.setShortcut('Ctrl+Z')
        redoAction = QtGui.QAction('Redo', self)
        redoAction.triggered.connect(self.project.redo)
        redoAction.setShortcut('Ctrl+Y')
        
        cutAction = QtGui.QAction('Cut', self)
        cutAction.triggered.connect(self.timelineWidget.cut)
        cutAction.setShortcut('Ctrl+X')
        copyAction = QtGui.QAction('Copy', self)
        copyAction.triggered.connect(self.timelineWidget.copy)
        copyAction.setShortcut('Ctrl+C')
        pasteAction = QtGui.QAction('Paste', self)
        pasteAction.triggered.connect(self.timelineWidget.paste)
        pasteAction.setShortcut('Ctrl+V')
        
        editMenu = menubar.addMenu('Edit')
        editMenu.addAction(undoAction)
        editMenu.addAction(redoAction)
        editMenu.addSeparator()
        editMenu.addAction(cutAction)
        editMenu.addAction(copyAction)
        editMenu.addAction(pasteAction)
        
        ### project menu ###
        newAction = QtGui.QAction('New', self)
        newAction.triggered.connect(self.newAction)
        cropAction = QtGui.QAction('Crop', self)
        cropAction.triggered.connect(self.cropAction)
        resizeAction = QtGui.QAction('Resize', self)
        resizeAction.triggered.connect(self.resizeAction)
        replacePaletteAction = QtGui.QAction('replace palette', self)
        replacePaletteAction.triggered.connect(self.replacePaletteAction)
        prefAction = QtGui.QAction('Background', self)
        prefAction.triggered.connect(self.backgroundAction)
        
        projectMenu = menubar.addMenu('Project')
        projectMenu.addAction(newAction)
        projectMenu.addAction(cropAction)
        projectMenu.addAction(resizeAction)
        projectMenu.addAction(replacePaletteAction)
        projectMenu.addAction(prefAction)

        ### resources menu ###
        savePaletteAction = QtGui.QAction('save  current palette', self)
        savePaletteAction.triggered.connect(self.savePaletteAction)
        savePenAction = QtGui.QAction('save custom pen', self)
        savePenAction.triggered.connect(self.savePenAction)
        reloadResourcesAction = QtGui.QAction('reload resources', self)
        reloadResourcesAction.triggered.connect(self.reloadResourcesAction)
        
        resourcesMenu = menubar.addMenu('Resources')
        resourcesMenu.addAction(savePaletteAction)
        resourcesMenu.addAction(savePenAction)
        resourcesMenu.addAction(reloadResourcesAction)
        
        ### view menu ###
        viewMenu = menubar.addMenu('View')
        dockWidgets = self.findChildren(QtGui.QDockWidget)
        for dock in dockWidgets:
            viewMenu.addAction(dock.toggleViewAction())
        viewMenu.addSeparator()
        self.lockLayoutWidget = QtGui.QAction('Lock Layout', self)
        self.lockLayoutWidget.setCheckable(True)
        self.lockLayoutWidget.setChecked(lock)
        self.lockLayoutWidget.toggled.connect(self.lockLayoutAction)
        viewMenu.addAction(self.lockLayoutWidget)
        
        ### shortcuts ###
        QtGui.QShortcut(QtCore.Qt.Key_Left, self, lambda : self.selectFrame(-1))
        QtGui.QShortcut(QtCore.Qt.Key_Right, self, lambda : self.selectFrame(1))
        QtGui.QShortcut(QtCore.Qt.Key_Up, self, lambda : self.selectLayer(-1))
        QtGui.QShortcut(QtCore.Qt.Key_Down, self, lambda : self.selectLayer(1))
        QtGui.QShortcut(QtCore.Qt.Key_Space, self, self.timelineWidget.playPauseClicked)
        QtGui.QShortcut(QtCore.Qt.Key_1, self, toolsDock.widget().penClicked)
        QtGui.QShortcut(QtCore.Qt.Key_2, self, toolsDock.widget().pipetteClicked)
        QtGui.QShortcut(QtCore.Qt.Key_3, self, toolsDock.widget().fillClicked)
        QtGui.QShortcut(QtCore.Qt.Key_4, self, toolsDock.widget().moveClicked)
        QtGui.QShortcut(QtCore.Qt.Key_5, self, toolsDock.widget().selectClicked)
        self.hiddenDock = []
        QtGui.QShortcut(QtCore.Qt.Key_Tab, self, self.hideDock)
        QtGui.QShortcut(QtCore.Qt.Key_E, self, self.project.changeColor)
        
        ### settings ###
        try:
            self.restoreGeometry(settings.value("geometry"))
        except TypeError:
            pass # no geometry to restore so leave as is
        try:
            self.restoreState(settings.value("windowState"))
        except TypeError:
            pass # no state to restore so leave as is
        settings.endGroup()
        self.show()

    ######## File menu #################################################
    def openAction(self):
        xml, url = open_pix(self.project.dirUrl)
        if xml and url:
            self.project.saveToUndo("all")
            self.project.importXml(xml)
            self.project.updateViewSign.emit()
            self.project.updatePaletteSign.emit()
            self.project.updateTimelineSign.emit()
            self.project.updateBackgroundSign.emit()
            self.project.updateFpsSign.emit()
            self.project.url = url
            self.project.dirUrl = os.path.dirname(url)

    def saveAsAction(self):
        url = get_save_url(self.project.dirUrl)
        if url:
            url = save_pix(self.project.exportXml(), url)
            if url:
                self.project.url = url
                self.project.dirUrl = os.path.dirname(url)
                self.project.saved = True
                self.updateTitle()
        
    def saveAction(self):
        if self.project.url:
            url = save_pix(self.project.exportXml(), self.project.url)
            if url:
                self.project.url = url
                self.project.dirUrl = os.path.dirname(url)
                self.project.saved = True
                self.updateTitle()
        else:
            self.saveAsAction()

    def importAsNewAction(self):
        urls = QtGui.QFileDialog.getOpenFileNames(
                    None, "Import PNG and GIF", 
                    self.project.dirUrl or os.path.expanduser("~"), 
                    "PNG and GIF files (*.png *.gif);;All files (*)")
        if not urls:
            return
        size, frames, colorTable = import_img(self.project, urls)
        if size and frames and colorTable:
            self.project.saveToUndo("all")
            self.project.initProject(size, colorTable, frames)
            self.project.updateViewSign.emit()
            self.project.updatePaletteSign.emit()
            self.project.updateTimelineSign.emit()
            
    def importAsLayerAction(self):
        urls = QtGui.QFileDialog.getOpenFileNames(
                    None, "Import PNG and GIF", 
                    self.project.dirUrl or os.path.expanduser("~"), 
                    "PNG and GIF files (*.png *.gif);;All files (*)")
        if urls:
            self.importAsLayer(urls)
            
    def importAsLayer(self, urls):
        size, frames, colorTable = import_img(self.project, urls,
                                              self.project.size,
                                              self.project.colorTable)
        if size and frames and colorTable:
            self.project.saveToUndo("all")
            self.project.importImg(size, colorTable, frames)
            self.project.updateViewSign.emit()
            self.project.updatePaletteSign.emit()
            self.project.updateTimelineSign.emit()
        
    def exportAction(self):
        export_png(self.project, self.project.dirUrl)
    
    def closeEvent(self, event):
        ret = True
        if not self.project.saved:
            message = QtGui.QMessageBox()
            message.setWindowTitle("Quit?")
            message.setText("Are you sure you want to quit?");
            message.setIcon(QtGui.QMessageBox.Warning)
            message.addButton("Cancel", QtGui.QMessageBox.RejectRole)
            message.addButton("Yes", QtGui.QMessageBox.AcceptRole)
            ret = message.exec_();
        if ret:
            settings = QtCore.QSettings()
            settings.beginGroup("mainWindow")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
            settings.setValue("lock", int(self.lockLayoutWidget.isChecked()))
            settings.endGroup()
            event.accept()
        else:
            event.ignore()
        
    ######## Project menu ##############################################
    def newAction(self):
        size, palette = NewDialog().getReturn()
        if size and palette:
            self.project.saveToUndo("all")
            self.project.initProject(size, palette)
            self.project.updateViewSign.emit()
            self.project.updatePaletteSign.emit()
            self.project.updateTimelineSign.emit()
            self.project.updateBackgroundSign.emit()
            self.project.updateFpsSign.emit()
            self.updateTitle()

    def cropAction(self):
        rect = CropDialog(self.project.size).getReturn()
        if rect:
            self.project.saveToUndo("size")
            self.project.timeline.applyToAllCanvas(
                    lambda c: Canvas(self.project, c.copy(rect)))
            self.project.size = rect.size()
            self.project.updateViewSign.emit()

    def resizeAction(self):
        newSize = ResizeDialog(self.project.size).getReturn()
        if newSize:
            self.project.saveToUndo("size")
            self.project.timeline.applyToAllCanvas(
                    lambda c: Canvas(self.project, c.scaled(newSize)))
            self.project.size = newSize
            self.project.updateViewSign.emit()
            
    def replacePaletteAction(self):
        url = QtGui.QFileDialog.getOpenFileName(None, "open palette file", 
                os.path.join("resources", "palette"), "Palette files (*.pal, *.gpl );;All files (*)")
        if url:
            pal = import_palette(url, len(self.project.colorTable))
            if pal:
                self.project.saveToUndo("colorTable_frames")
                self.project.changeColorTable(pal)
                self.project.color = 1
                self.project.updateViewSign.emit()
                self.project.updatePaletteSign.emit()
                self.project.colorChangedSign.emit()
        
    def backgroundAction(self):
        color, pattern = BackgroundDialog(self.project.bgColor,
                                self.project.bgPattern).getReturn()
        if color and pattern:
            self.project.saveToUndo("background")
            self.project.bgColor = color
            self.project.bgPattern = pattern
            self.project.updateBackgroundSign.emit()

    def savePaletteAction(self):
        url = get_save_url(os.path.join("resources", "palette"), "pal")
        pal = export_palette(self.project.colorTable)
        if url:
            try:
                save = open(url, "w")
                save.write(pal)
                save.close()
                print("saved")
            except IOError:
                print("Can't open file")
        
    def savePenAction(self):
        if self.project.penDict["custom"]:
            url = get_save_url(os.path.join("resources", "pen"), "py")
            pen = export_pen(self.project.penDict["custom"], os.path.splitext(os.path.basename(url))[0])
            if url:
                try:
                    save = open(url, "w")
                    save.write(pen)
                    save.close()
                    print("saved")
                except IOError:
                    print("Can't open file")

    def reloadResourcesAction(self):
        self.project.importResources()
        self.toolsWidget.penWidget.loadPen()
        self.toolsWidget.brushWidget.loadBrush()
        
    ######## View menu ##############################################
    def lockLayoutAction(self, check):
        for dock in self.findChildren(QtGui.QDockWidget):
            dock.lock(check)
    
    def hideDock(self):
        hide = False
        for dock in self.findChildren(QtGui.QDockWidget):
            if dock.isVisible():
                hide = True
        if hide:
            self.hiddenDock = []
            for dock in self.findChildren(QtGui.QDockWidget):
                if dock.isVisible():
                    self.hiddenDock.append(dock.objectName())
                    dock.hide()
        elif self.hiddenDock:
            for dock in self.findChildren(QtGui.QDockWidget):
                if dock.objectName() in self.hiddenDock:
                    dock.show()
        else:
            for dock in self.findChildren(QtGui.QDockWidget):
                dock.show()
            
    ######## Shortcuts #################################################
    def selectFrame(self, n):
        exf = self.project.curFrame
        f = self.project.curFrame + n
        lf = self.project.timeline.frameVisibleCount()
        if f < 0:
            if self.project.loop:
                self.project.curFrame = lf -1
        elif f >= lf:
            if self.project.loop:
                self.project.curFrame = 0
            else: 
                self.project.curFrame = f
        else:
            self.project.curFrame = f
        if self.project.curFrame != exf:
            self.project.updateTimelineSign.emit()
            self.project.updateViewSign.emit()

    def selectLayer(self, n):
        if 0 <= self.project.curLayer+n < len(self.project.timeline):
            self.project.curLayer += n
            self.project.updateTimelineSign.emit()
            self.project.updateViewSign.emit()
            
    def updateTitle(self):
        url, sav = "untitled", "* "
        if self.project.saved:
            sav = ""
        if self.project.url:
            url = os.path.basename(self.project.url)
        self.setWindowTitle("%s%s - pixeditor" %(sav, url))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
            l = []
            for url in event.mimeData().urls():
                l.append(url.toLocalFile())
            self.dropped.emit(l)
        else:
            event.ignore()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap("icons/pixeditor.png")))
    mainWin = MainWindow()
    sys.exit(app.exec_())

