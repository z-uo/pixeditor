#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Copyright Nicolas Bougère (pops451@gmail.com), 2012-2013
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

# add texture
# fill all similar color
# add animated gif export


# Python 3 Compatibility
from __future__ import division
from __future__ import print_function

import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt

from data import Project
from dialogs import *
from import_export import *
from timeline import TimelineWidget
from widget import Background, Button, Viewer
from colorPicker import ColorDialog

def pointToInt(point):
    return QtCore.QPoint(int(point.x()), int(point.y()))

def pointToFloat(point):
    return QtCore.QPointF(int(point.x()), int(point.y()))
        
def get_rect(rect):
    w = int(rect.width())
    h = int(rect.height())
    if w < 0:
        x = int(rect.x()) + w
        w = int(rect.x()) - x
    else:
        x = int(rect.x())
    if h < 0:
        y = int(rect.y()) + h
        h = int(rect.y()) - y
    else:
        y = int(rect.y())
    return QtCore.QRect(x, y, w, h)
    
class SelectionRect(QtGui.QGraphicsRectItem):
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
        

class Scene(QtGui.QGraphicsView):
    """ Display, zoom, pan..."""
    def __init__(self, project):
        QtGui.QGraphicsView.__init__(self)
        self.project = project
        self.zoomN = 1
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
        # background
        self.setBackgroundBrush(QtGui.QBrush(self.project.bg_color))
        self.bg = self.scene.addPixmap(
                    Background(self.project.size, self.project.bg_pattern))
        # frames
        self.itemList = []
        self.canvasList = []
        #sellection
        self.selRect = None
        # OnionSkin
        p = QtGui.QPixmap(self.project.size)
        self.onionPrevItem = self.scene.addPixmap(p)
        self.onionPrevItem.setZValue(101)
        self.onionPrevItem.setOpacity(0.5)
        self.onionPrevItem.hide()
        p = QtGui.QPixmap(self.project.size)
        self.onionNextItem = self.scene.addPixmap(p)
        self.onionNextItem.setZValue(102)
        self.onionNextItem.setOpacity(0.5)
        self.onionNextItem.hide()
        # pen
        self.penItem = QtGui.QGraphicsRectItem(0, 0, 1, 1)
        self.penItem.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 0)))
        self.penItem.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.scene.addItem(self.penItem)
        self.penItem.setZValue(103)
        self.penItem.hide()
        self.project.pen_changed.connect(self.change_pen)
        self.project.tool_changed.connect(self.change_pen)
        self.project.color_changed.connect(self.change_pen)
        self.change_pen()

        self.project.update_view.connect(self.change_frame)
        self.project.update_background.connect(self.update_background)
        self.change_frame()

    def change_pen(self):
        for i in self.penItem.childItems():
            self.scene.removeItem(i)
        if self.project.tool == "pen":
            pen = QtGui.QPen(QtCore.Qt.NoPen)
            brush = QtGui.QColor(self.project.colorTable[self.project.color])
            for i in self.project.pen:
                p = QtGui.QGraphicsRectItem(i[0], i[1], 1, 1, self.penItem)
                p.setPen(pen)
                p.setBrush(brush)
                
    def update_background(self):
        self.setBackgroundBrush(QtGui.QBrush(self.project.bg_color))
        self.bg.setPixmap(Background(self.project.size, 
                                     self.project.bg_pattern))
        
    def change_frame(self):
        self.canvasList = self.project.timeline.get_canvas_list(self.project.curFrame)
        # resize scene if needed
        if self.scene.sceneRect().size().toSize() != self.project.size:
            self.scene.setSceneRect(0, 0, 
                    self.project.size.width(), self.project.size.height())
            self.update_background()
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
            else:
                self.itemList[n].setVisible(False)
        # onionskin
        layer = self.project.timeline[self.project.curLayer]
        if not self.project.playing and self.project.onionSkinPrev:
            frame = self.project.curFrame
            prev = False
            while 0 <= frame < len(layer):
                if layer[frame]:
                    if frame == 0 and self.project.loop:
                        prev = layer.get_canvas(len(layer)-1)
                    else:
                        prev = layer.get_canvas(frame-1)
                    if prev and prev != layer.get_canvas(self.project.curFrame):
                        self.onionPrevItem.pixmap().convertFromImage(prev)
                        self.onionPrevItem.show()
                    else:
                        self.onionPrevItem.hide()
                    break
                frame -= 1
            else:
                self.onionPrevItem.hide()
        else:
            self.onionPrevItem.hide()
        if not self.project.playing and self.project.onionSkinNext:
            frame = self.project.curFrame + 1
            nex = False
            while 0 <= frame < len(layer):
                if layer[frame]:
                    self.onionNextItem.pixmap().convertFromImage(layer[frame])
                    self.onionNextItem.show()
                    break
                frame += 1
            else:
                if (frame == len(layer) and self.project.loop and 
                    layer[0] != layer.get_canvas(self.project.curFrame)):
                    self.onionNextItem.pixmap().convertFromImage(layer[0])
                    self.onionNextItem.show()
                else:
                    self.onionNextItem.hide()
        else:
            self.onionNextItem.hide()

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
        elif (event.buttons() == QtCore.Qt.LeftButton and
                self.canvasList[l] and self.project.timeline[l].visible):
            pos = self.pointToInt(self.mapToScene(event.pos()))
            if self.project.tool == "move":
                self.lastPos = pos
            elif self.project.tool == "select":
                self.selRect = SelectionRect(pos)
                self.selRect.setZValue(103)
                self.scene.addItem(self.selRect)
            else:
                self.canvasList[l].clic(pos)
                self.itemList[l].pixmap().convertFromImage(self.canvasList[l])
                self.itemList[l].update()
        else:
            return QtGui.QGraphicsView.mousePressEvent(self, event)

    def enterEvent(self, event):
        self.penItem.show()

    def leaveEvent(self, event):
        self.penItem.hide()

    def mouseMoveEvent(self, event):
        self.penItem.show()
        self.penItem.setPos(self.pointToFloat(self.mapToScene(event.pos())))
        l = self.project.curLayer
        # pan
        if event.buttons() == QtCore.Qt.MidButton:
            globalPos = QtGui.QCursor.pos()
            self.horizontalScrollBar().setValue(self.startScroll[0] -
                    globalPos.x() + self.lastPos.x())
            self.verticalScrollBar().setValue(self.startScroll[1] -
                    globalPos.y() + self.lastPos.y())
        # draw on canvas
        elif (event.buttons() == QtCore.Qt.LeftButton
                and self.canvasList[l] and self.project.timeline[l].visible):
            pos = self.pointToInt(self.mapToScene(event.pos()))
            if self.project.tool == "move":
                dif = pos - self.lastPos
                intPos = self.pointToInt(self.itemList[l].pos())
                self.itemList[l].setPos(QtCore.QPointF(intPos + dif))
                self.lastPos = pos
            elif self.project.tool == "select": 
                self.selRect.scale(pos)
            else:
                self.canvasList[l].move(pos)
                self.itemList[l].pixmap().convertFromImage(self.canvasList[l])
                self.itemList[l].update()
        else:
            return QtGui.QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            l = self.project.curLayer
            if self.project.tool == "move" and self.canvasList[l] and self.itemList[l].pos():
                    offset = (int(self.itemList[l].pos().x()), 
                              int(self.itemList[l].pos().y()))
                    self.canvasList[l].load_from_list(
                                        self.canvasList[l].return_as_list(),
                                        self.canvasList[l].width(), offset)
                    self.itemList[l].setPos(QtCore.QPointF(0, 0))
                    self.change_frame()
            elif self.project.tool == "select": 
                rect = get_rect(self.selRect.rect())
                if rect.isValid():
                    sel = self.canvasList[l].return_as_matrix(rect)
                    self.canvasList[l].draw_rect(rect, 0)
                    self.project.set_custom_pen.emit(sel)
                    self.change_frame()
                self.scene.removeItem(self.selRect)
                del self.selRect
        else:
            return QtGui.QGraphicsView.mouseReleaseEvent(self, event)


class PaletteCanvas(QtGui.QWidget):
    """ Canvas where the palette is draw """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setFixedSize(164, 644)
        self.background = QtGui.QBrush(self.parent.project.bg_color)
        self.alpha = QtGui.QPixmap("icons/color_alpha.png")
        self.black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        self.white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        self.parent.project.update_background.connect(self.update_background)
        
    def update_background(self):
         self.background = QtGui.QBrush(self.parent.project.bg_color)
         self.update()
         
    def paintEvent(self, ev=''):
        p = QtGui.QPainter(self)
        p.fillRect (0, 0, self.width(), self.height(), self.background)
        for n, i in enumerate(self.parent.project.colorTable):
            y = ((n // 8) * 20) + 2
            x = ((n % 8) * 20) + 2
            if n == self.parent.project.color:
                p.fillRect (x, y, 20, 20, self.black)
                p.fillRect (x+1, y+1, 18, 18, self.white)
            p.drawPixmap(x+2, y+2, self.alpha)
            p.fillRect(x+2, y+2, 16, 16, QtGui.QBrush(QtGui.QColor().fromRgba(i)))

    def event(self, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress and
                       event.button()==QtCore.Qt.LeftButton):
            item = self.item_at(event.x(), event.y())
            if item is not None:
                self.parent.project.set_color(item)
        elif (event.type() == QtCore.QEvent.MouseButtonDblClick and
                       event.button()==QtCore.Qt.LeftButton):
            item = self.item_at(event.x(), event.y())
            if item is not None:
                self.parent.edit_color(item)
        return QtGui.QWidget.event(self, event)
        
    def item_at(self, x, y):
        x, y = ((x-2) // 20), ((y-2) // 20)
        if y == 0:
            s = x
        else:
            s = (y * 8) + x
        if s >= 0 and s < len(self.parent.project.colorTable):
            return s
        return None


class ToolsWidget(QtGui.QWidget):
    """ side widget cantaining tools buttons and palette """
    change_pen = QtCore.pyqtSignal(str)
    def __init__(self, project):
        QtGui.QWidget.__init__(self)
        self.project = project

        ### tools buttons ###
        self.penB = Button("pen", "icons/tool_pen.png", self.pen_tool_clicked, True)
        self.pipetteB = Button("pipette", "icons/tool_pipette.png", self.pipette_tool_clicked, True)
        self.fillB = Button("fill", "icons/tool_fill.png", self.fill_tool_clicked, True)
        self.moveB = Button("move", "icons/tool_move.png", self.move_tool_clicked, True)
        self.penB.setChecked(True)
        self.selectB = Button("select", "icons/tool_select.png", self.select_tool_clicked, True)

        ### pen size ###
        self.penW = QtGui.QComboBox(self)
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_1.png")), "point")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_2_hori.png")), "2 pixels horizontal")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_2_vert.png")), "2 pixels vertical")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_2x2_square.png")), "2x2 square")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_3x3_square.png")), "3x3 square")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_3x3_cross.png")), "3x3 cross")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_5x5_round.png")), "5x5 round")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_5x5_round.png")), "5x5 round")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_custom.png")), "custom")
        self.penW.activated[str].connect(self.pen_chooser_clicked)
        self.penDict = { "point" : ((0, 0),),
                         "2 pixels horizontal" : ((0, 0), (1, 0)),
                         "2 pixels vertical" : ((0, 0),
                                                (0, 1)),
                         "2x2 square" : ((0, 0), (0, 1),
                                         (1, 0), (1, 1)),
                         "3x3 square" : ((-1, -1), (-1, 0), (-1, 1),
                                         ( 0, -1), ( 0, 0), ( 0, 1),
                                         ( 1, -1), ( 1, 0), ( 1, 1)),
                         "3x3 cross" : ((-1, 0),
                               (0, -1), ( 0, 0), (0, 1),
                                        ( 1, 0)),
                        "5x5 round" : ((-1, -2), (0, -2), (1, -2),
                             (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1),
                             (-2,  0), (-1,  0), (0,  0), (1,  0), (2,  0),
                             (-2,  1), (-1,  1), (0,  1), (1,  1), (2,  1),
                                       (-1,  2), (0,  2), (1,  2)),
                        "custom" : ()
                        }
        self.project.set_custom_pen.connect(self.set_custom_pen)

        ### palette ###
        self.paletteCanvas = PaletteCanvas(self)
        self.paletteV = Viewer()
        self.paletteV.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.paletteV.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.paletteV.setWidget(self.paletteCanvas)
        
        self.project.update_palette.connect(self.paletteCanvas.update)
        addColorB = Button("add color",
            "icons/color_add.png", self.add_color_clicked)
        delColorB = Button("delete color",
            "icons/color_del.png", self.del_color_clicked)
        moveLeftColorB = Button("move color left",
            "icons/color_move_left.png", self.move_color_left_clicked)
        moveRightColorB = Button("move color right",
            "icons/color_move_right.png", self.move_color_right_clicked)

        ### Layout ###
        tools = QtGui.QVBoxLayout()
        tools.setSpacing(0)
        tools.addWidget(self.penB)
        tools.addWidget(self.pipetteB)
        tools.addWidget(self.fillB)
        tools.addWidget(self.moveB)
        tools.addWidget(self.selectB)
        tools.addStretch()
        colors = QtGui.QHBoxLayout()
        colors.setSpacing(0)
        colors.addWidget(addColorB)
        colors.addWidget(delColorB)
        colors.addWidget(moveLeftColorB)
        colors.addWidget(moveRightColorB)
        layout = QtGui.QGridLayout()
        layout.setSpacing(4)
        layout.addLayout(tools, 0, 0, 3, 1)
        layout.addWidget(self.penW, 0, 1)
        layout.addWidget(self.paletteV, 1, 1)
        layout.addLayout(colors, 2, 1)
        self.setLayout(layout)

    def showEvent(self, event):
        self.paletteV.setMinimumWidth(self.paletteCanvas.width() + 
                    self.paletteV.verticalScrollBar().width() + 2)

    ######## Tools #####################################################
    def pen_tool_clicked(self):
        self.project.tool = "pen"
        self.penB.setChecked(True)
        self.pipetteB.setChecked(False)
        self.fillB.setChecked(False)
        self.moveB.setChecked(False)
        self.selectB.setChecked(False)
        self.project.tool_changed.emit()

    def pipette_tool_clicked(self):
        self.project.tool = "pipette"
        self.penB.setChecked(False)
        self.fillB.setChecked(False)
        self.pipetteB.setChecked(True)
        self.moveB.setChecked(False)
        self.selectB.setChecked(False)
        self.project.tool_changed.emit()

    def fill_tool_clicked(self):
        self.project.tool = "fill"
        self.fillB.setChecked(True)
        self.pipetteB.setChecked(False)
        self.penB.setChecked(False)
        self.moveB.setChecked(False)
        self.selectB.setChecked(False)
        self.project.tool_changed.emit()

    def move_tool_clicked(self):
        self.project.tool = "move"
        self.fillB.setChecked(False)
        self.pipetteB.setChecked(False)
        self.penB.setChecked(False)
        self.moveB.setChecked(True)
        self.selectB.setChecked(False)
        self.project.tool_changed.emit()

    def select_tool_clicked(self):
        self.project.tool = "select"
        self.fillB.setChecked(False)
        self.pipetteB.setChecked(False)
        self.penB.setChecked(False)
        self.moveB.setChecked(False)
        self.selectB.setChecked(True)
        self.project.tool_changed.emit()

    def pen_chooser_clicked(self, text):
        self.project.pen = self.penDict[str(text)]
        self.project.pen_changed.emit()
        
    def set_custom_pen(self, li):
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
            self.penDict["custom"] = nLi
            self.penW.setCurrentIndex(self.penW.findText("custom"))
            self.pen_tool_clicked()
            self.pen_chooser_clicked("custom")
        
    ######## Color #####################################################
    def edit_color(self, n):
        col = self.project.colorTable[self.project.color]
        ok, color = ColorDialog(True, col).get_rgba()
        if not ok:
            return
        self.project.save_to_undo("colorTable")
        self.project.colorTable[n] = color
        for i in self.project.timeline.get_all_canvas():
            i.setColorTable(self.project.colorTable)
        self.project.update_view.emit()
        self.paletteCanvas.update()
        self.project.color_changed.emit()

    def add_color_clicked(self):
        """ select a color and add it to the palette"""
        if not len(self.project.colorTable) >= 256:
            col = self.project.colorTable[self.project.color]
            ok, color = ColorDialog(True, col).get_rgba()
            if not ok:
                return
            self.project.save_to_undo("colorTable_frames")
            self.project.colorTable.append(color)
            self.project.set_color(len(self.project.colorTable)-1)
            for i in self.project.timeline.get_all_canvas():
                i.setColorTable(self.project.colorTable)
            self.project.update_view.emit()

    def del_color_clicked(self):
        col, table = self.project.color, self.project.colorTable
        if col != 0:
            self.project.save_to_undo("colorTable_frames")
            table.pop(col)
            for i in self.project.timeline.get_all_canvas():
                i.merge_color(col, 0)
                i.setColorTable(table)
            self.project.set_color(col-1)
            self.project.update_view.emit()

    def move_color_left_clicked(self):
        col, table = self.project.color, self.project.colorTable
        if col != 0:
            self.project.save_to_undo("colorTable_frames")
            table[col], table[col-1] = table[col-1], table[col]
            for i in self.project.timeline.get_all_canvas():
                i.swap_color(col, col-1)
                i.setColorTable(table)
            self.project.set_color(col-1)

    def move_color_right_clicked(self):
        col, table = self.project.color, self.project.colorTable
        if col != len(table)-1:
            self.project.save_to_undo("colorTable_frames")
            table[col], table[col+1] = table[col+1], table[col]
            for i in self.project.timeline.get_all_canvas():
                i.swap_color(col, col+1)
                i.setColorTable(table)
            self.project.set_color(col+1)


class MainWindow(QtGui.QMainWindow):
    """ Main windows of the application """
    currentFrameChanged = QtCore.pyqtSignal(object)
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("pixeditor")

        self.project = Project(self)
        self.toolsWidget = ToolsWidget(self.project)
        self.timelineWidget = TimelineWidget(self.project)
        self.scene = Scene(self.project)

        ### File menu ###
        menubar = self.menuBar()
        openAction = QtGui.QAction('Open', self)
        openAction.triggered.connect(self.open_action)
        saveAsAction = QtGui.QAction('Save as', self)
        saveAsAction.triggered.connect(self.save_as_action)
        saveAction = QtGui.QAction('Save', self)
        saveAction.triggered.connect(self.save_action)
        saveAction.setShortcut('Ctrl+S')
        
        importAction = QtGui.QAction('Import as new project', self)
        importAction.triggered.connect(self.import_as_new_action)
        exportAction = QtGui.QAction('Export', self)
        exportAction.triggered.connect(self.export_action)
        exportAction.setShortcut('Ctrl+E')
        
        exitAction = QtGui.QAction('Exit', self)
        exitAction.triggered.connect(self.exit_action)
        exitAction.setShortcut('Ctrl+Q')
        
        fileMenu = menubar.addMenu('File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(saveAction)
        fileMenu.addSeparator()
        fileMenu.addAction(importAction)
        fileMenu.addAction(exportAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)
        
        ### Edit menu ###
        undoAction = QtGui.QAction('Undo', self)
        undoAction.triggered.connect(self.undo)
        undoAction.setShortcut('Ctrl+Z')
        redoAction = QtGui.QAction('Redo', self)
        redoAction.triggered.connect(self.redo)
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
        newAction.triggered.connect(self.new_action)
        cropAction = QtGui.QAction('Crop', self)
        cropAction.triggered.connect(self.crop_action)
        resizeAction = QtGui.QAction('Resize', self)
        resizeAction.triggered.connect(self.resize_action)
        prefAction = QtGui.QAction('Background', self)
        prefAction.triggered.connect(self.background_action)
        
        projectMenu = menubar.addMenu('Project')
        projectMenu.addAction(newAction)
        projectMenu.addAction(cropAction)
        projectMenu.addAction(resizeAction)
        projectMenu.addAction(prefAction)

        ### shortcuts ###
        shortcut = QtGui.QShortcut(self)
        shortcut.setKey(QtCore.Qt.Key_Left)
        shortcut.activated.connect(lambda : self.select_frame(-1))
        shortcut2 = QtGui.QShortcut(self)
        shortcut2.setKey(QtCore.Qt.Key_Right)
        shortcut2.activated.connect(lambda : self.select_frame(1))
        shortcut3 = QtGui.QShortcut(self)
        shortcut3.setKey(QtCore.Qt.Key_Up)
        shortcut3.activated.connect(lambda : self.select_layer(-1))
        shortcut4 = QtGui.QShortcut(self)
        shortcut4.setKey(QtCore.Qt.Key_Down)
        shortcut4.activated.connect(lambda : self.select_layer(1))
        shortcut5 = QtGui.QShortcut(self)
        shortcut5.setKey(QtCore.Qt.Key_Space)
        shortcut5.activated.connect(self.timelineWidget.play_pause_clicked)

        ### layout #####################################################
        splitter = QtGui.QSplitter()
        splitter.addWidget(self.toolsWidget)
        splitter.addWidget(self.scene)
        splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
        splitter2.addWidget(splitter)
        splitter2.addWidget(self.timelineWidget)
        self.setCentralWidget(splitter2)
        
        
        #~ self.setDockNestingEnabled(True)
        #~ self.setCentralWidget(self.scene)
        #~ leftDock = QtGui.QDockWidget("tools")
        #~ leftDock.setWidget(self.toolsWidget)
        #~ self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, leftDock)
        #~ 
        #~ bottomDock = QtGui.QDockWidget("timeline")
        #~ bottomDock.setWidget(self.timelineWidget)
        #~ self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, bottomDock)
        
        self.show()
        
    ######## File menu #################################################
    def open_action(self):
        size, frames, colorTable, url = open_pix(self.project)
        if size and frames and colorTable and url:
            self.project.save_to_undo("all")
            self.setWindowTitle("pixeditor | %s" %(os.path.basename(url)))
            self.project.init_project(size, frames, colorTable, url)
            self.project.update_view.emit()
            self.project.update_palette.emit()
            self.project.update_timeline.emit()

    def save_as_action(self):
        url = save_pix_as(self.project)
        if url:
            self.project.url = url
            self.setWindowTitle("pixeditor | %s" %(os.path.basename(url)))
        
    def save_action(self):
        if self.project.url:
            save_pix(self.project, self.project.url)
        else:
            self.save_as_action()

    def import_as_new_action(self):
        size, frames, colorTable = import_png(self.project)
        if size and frames and colorTable:
            self.project.save_to_undo("all")
            self.setWindowTitle("pixeditor")
            self.project.init_project(size, [{"frames": frames, "name": "import"}], colorTable)
            self.project.update_view.emit()
            self.project.update_palette.emit()
            self.project.update_timeline.emit()
    
    def export_action(self):
        export_png(self.project)

    def exit_action(self):
        message = QtGui.QMessageBox()
        message.setWindowTitle("Quit?")
        message.setText("Are you sure you want to quit?");
        message.setIcon(QtGui.QMessageBox.Warning)
        message.addButton("Cancel", QtGui.QMessageBox.RejectRole)
        message.addButton("Yes", QtGui.QMessageBox.AcceptRole)
        ret = message.exec_();
        if ret:
            QtGui.qApp.quit()

    ######## Edit menu #################################################
    def undo(self):
        self.project.undo()
        self.project.update_view.emit()
        self.project.update_timeline.emit()

    def redo(self):
        self.project.redo()
        self.project.update_view.emit()
        self.project.update_timeline.emit()
        
    ######## Project menu ##############################################
    def new_action(self):
        size = NewDialog().get_return()
        if size:
            self.project.save_to_undo("all")
            self.project.init_project(size)
            self.project.update_view.emit()
            self.project.update_palette.emit()
            self.project.update_timeline.emit()
            self.setWindowTitle("pixeditor")

    def crop_action(self):
        rect = CropDialog(self.project.size).get_return()
        if rect:
            self.project.timeline.apply_to_all(
                    lambda c: Canvas(self.project, c.copy(rect)))
            self.project.size = rect.size()
            self.project.update_view.emit()

    def resize_action(self):
        factor = ResizeDialog(self.project.size).get_return()
        if factor and factor != 1:
            self.project.save_to_undo("canvas_size")
            newSize = self.project.size*factor
            self.project.timeline.apply_to_all(
                    lambda c: Canvas(self.project, c.scaled(newSize)))
            self.project.size = newSize
            self.project.update_view.emit()
            
    def background_action(self):
        color, pattern = BackgroundDialog(self.project.bg_color,
                                self.project.bg_pattern).get_return()
        if color and pattern:
            self.project.save_to_undo("background")
            self.project.bg_color = color
            self.project.bg_pattern = pattern
            self.project.update_background.emit()

    ######## Shortcuts #################################################
    def select_frame(self, n):
        maxF = max([len(l) for l in self.project.timeline])
        if 0 <= self.project.curFrame+n < maxF:
            self.project.curFrame += n
            self.project.update_timeline.emit()
            self.project.update_view.emit()

    def select_layer(self, n):
        if 0 <= self.project.curLayer+n < len(self.project.timeline):
            self.project.curLayer += n
            self.project.update_timeline.emit()
            self.project.update_view.emit()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap("icons/pixeditor.png")))
    mainWin = MainWindow()
    sys.exit(app.exec_())

