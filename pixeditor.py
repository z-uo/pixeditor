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


# add more control on palette
# add a tool to make lines (iso...)
# add choice between a gif or png transparency mode
# add a cursor layer (pixel who will be paint) grid
# add animated gif export


# Python 3 Compatibility
from __future__ import division
from platform import python_version_tuple
if int(python_version_tuple()[0]) >= 3:
    xrange = range

import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt

from dialogs import *
from import_export import *
from timeline import *
from widget import *

DEFAUT_COLOR = 1
DEFAUT_SIZE = (64, 64)
DEFAUT_COLORTABLE = (QtGui.qRgba(0, 0, 0, 0), QtGui.qRgba(0, 0, 0, 255))
DEFAUT_PEN = ((0, 0),)
DEFAUT_TOOL = "pen"
        
import array
import time

        
class Bg(QtGui.QPixmap):
    """ background of the scene"""
    def __init__(self, w, h):
        QtGui.QPixmap.__init__(self, w, h)
        self.brush = QtGui.QBrush(QtGui.QPixmap("icons/bg.png"))
        self.fill(QtGui.QColor(0, 0, 0, 0))
        p = QtGui.QPainter(self)
        p.fillRect (0,0, w, h, self.brush)
    
class Border(QtGui.QPixmap):
    """ background of the scene"""
    def __init__(self, w, h):
        QtGui.QPixmap.__init__(self, w+2, h+2)
        self.fill(QtGui.QColor(255, 255, 255, 0))
        p = QtGui.QPainter(self)
        p.setPen(QtGui.QPen(QtGui.QColor(70, 70, 70)))
        p.drawLine (0, 0, w+1, 0)
        p.drawLine (w+1, 0, w+1, h+1)
        p.drawLine (w+1, h+1, 0, h+1)
        p.drawLine (0, h, 0, 0)

class Scene(QtGui.QGraphicsView):
    """ Display, zoom, pan..."""
    def __init__(self, project):
        QtGui.QGraphicsView.__init__(self)
        self.project = project
        self.zoomN = 1
        w, h = self.project.size[0], self.project.size[1]
        # scene
        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.setScene(self.scene)
        self.setTransformationAnchor(
                QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.setMinimumSize(400, 400)
        self.scene.setSceneRect(0, 0, w, h)
        # background
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(150, 150, 150)))
        self.bg = self.scene.addPixmap(Bg(w, h))
        self.border = self.scene.addPixmap(Border(w, h))
        self.border.setPos(-1, -1)
        # frames
        self.itemList = []
        self.canvasList = []
        # OnionSkin
        p = QtGui.QPixmap(w, h)
        self.onionPrevItem = self.scene.addPixmap(p)
        self.onionPrevItem.setZValue(101)
        self.onionPrevItem.setOpacity(0.5)
        self.onionPrevItem.hide()
        p = QtGui.QPixmap(w, h)
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
        
    def change_frame(self):
        # resize scene if needed
        w, h = self.project.size[0], self.project.size[1]
        if (int(self.scene.sceneRect().width()) != w or
            int(self.scene.sceneRect().height()) != h):
            self.scene.setSceneRect(0, 0, w, h)
            self.bg.setPixmap(Bg(w, h))
            self.border.setPixmap(Border(w, h))
        # init item hanging canvas if needed
        self.canvasList = self.project.get_canvas_list()
        if len(self.itemList) != len(self.canvasList):
            for i in self.itemList:
                self.scene.removeItem(i)
            self.itemList = []
            for i in self.canvasList:
                p = QtGui.QPixmap(self.scene.width(), self.scene.height())
                self.itemList.append(self.scene.addPixmap(p))
            z = 100
            for i in self.itemList:
                i.setZValue(z)
                z -= 1
        # updates canvas
        for n, i in enumerate(self.canvasList):
            if i and self.project.frames[n]["visible"]:
                self.itemList[n].setVisible(True)
                self.itemList[n].pixmap().convertFromImage(i)
                self.itemList[n].update()
            else:
                self.itemList[n].setVisible(False)
        # onionskin
        if self.project.onionSkinPrev and not self.project.playing:
            prev = self.project.get_prev_canvas()
            if prev:
                self.onionPrevItem.pixmap().convertFromImage(prev)
                self.onionPrevItem.show()
            else:
                self.onionPrevItem.hide()
        else:
            self.onionPrevItem.hide()
        if self.project.onionSkinNext and not self.project.playing:
            nex = self.project.get_next_canvas()
            if nex:
                self.onionNextItem.pixmap().convertFromImage(nex)
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
        l = self.project.currentLayer
        # pan
        if event.buttons() == QtCore.Qt.MidButton:
            self.startScroll = (self.horizontalScrollBar().value(),
                                self.verticalScrollBar().value())
            self.lastPos = QtCore.QPoint(QtGui.QCursor.pos())
            self.setDragMode(QtGui.QGraphicsView.NoDrag)
        # draw on canvas
        elif (event.buttons() == QtCore.Qt.LeftButton and 
                self.canvasList[l] and self.project.frames[l]["visible"]):
            pos = self.pointToInt(self.mapToScene(event.pos()))
            if self.project.tool == "move":
                self.lastPos = pos
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
        l = self.project.currentLayer
        # pan
        if event.buttons() == QtCore.Qt.MidButton:
            globalPos = QtGui.QCursor.pos()
            self.horizontalScrollBar().setValue(self.startScroll[0] -
                    globalPos.x() + self.lastPos.x())
            self.verticalScrollBar().setValue(self.startScroll[1] -
                    globalPos.y() + self.lastPos.y())
        # draw on canvas
        elif (event.buttons() == QtCore.Qt.LeftButton 
                and self.canvasList[l] and self.project.frames[l]["visible"]):
            pos = self.pointToInt(self.mapToScene(event.pos()))
            if self.project.tool == "move":
                dif = pos - self.lastPos
                intPos = self.pointToInt(self.itemList[l].pos())
                self.itemList[l].setPos(QtCore.QPointF(intPos + dif))
                self.lastPos = pos
            else:
                self.canvasList[l].move(pos)
                self.itemList[l].pixmap().convertFromImage(self.canvasList[l])
                self.itemList[l].update()
        else:
            return QtGui.QGraphicsView.mouseMoveEvent(self, event)
            
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.project.tool == "move":
            l = self.project.currentLayer
            if self.canvasList[l] and self.itemList[l].pos():
                offset = (int(self.itemList[l].pos().x()), int(self.itemList[l].pos().y()))
                self.canvasList[l].load_from_list(self.canvasList[l].return_as_list(), 
                                                  self.canvasList[l].width(),
                                                  offset)
                self.itemList[l].setPos(QtCore.QPointF(0, 0))
                self.change_frame()
        else:
            return QtGui.QGraphicsView.mouseReleaseEvent(self, event)


class Canvas(QtGui.QImage):
    """ Canvas for drawing"""
    def __init__(self, project, w, h=None):
        self.project = project
        if not h:
            QtGui.QImage.__init__(self, w)
        else:
            QtGui.QImage.__init__(self, w, h, QtGui.QImage.Format_Indexed8)
            self.setColorTable(self.project.colorTable)
            self.fill(0)

        self.lastPoint = False
        self.undoList = []
        self.redoList = []

    ######## import/export #############################################
    def load_from_list(self, li, exWidth=None, offset=(0, 0)):
        self.fill(0)
        if not exWidth:
            exWidth = self.width()
        x, y = 0, 0
        for i in li:
            nx, ny = x + offset[0], y + offset[1]
            if self.rect().contains(nx, ny):
                self.setPixel(QtCore.QPoint(nx, ny), int(i))
            x += 1
            if x >= exWidth:
                x = 0
                y += 1

    def return_as_list(self):
        l = []
        for y in xrange(self.height()):
            for x in xrange(self.width()):
                l.append(self.pixelIndex(x, y))
        return l
        
    def merge_color(self, exCol, newCol):
        for y in xrange(self.height()):
            for x in xrange(self.width()):
                if self.pixelIndex(x, y) == exCol:
                    self.setPixel(x, y, newCol)
                    
    def swap_color(self, col1, col2):
        for y in xrange(self.height()):
            for x in xrange(self.width()):
                if self.pixelIndex(x, y) == col1:
                    self.setPixel(x, y, col2)
                elif self.pixelIndex(x, y) == col2:
                    self.setPixel(x, y, col1)
        
    ######## undo/redo #################################################
    def save_to_undo(self):
        self.undoList.append(Canvas(self.project, self))
        if len(self.undoList) > 50:
            self.undoList.pop(0)
        self.redoList = []

    def undo(self):
        if len(self.undoList) > 0:
            self.redoList.append(Canvas(self.project, self))
            if len(self.redoList) > 50:
                self.redoList.pop(0)
            self.swap(self.undoList.pop(-1))

    def redo(self):
        if len(self.redoList) > 0:
            self.undoList.append(Canvas(self.project, self))
            if len(self.undoList) > 50:
                self.undoList.pop(0)
            self.swap(self.redoList.pop(-1))
        
    ######## draw ######################################################
    def clear(self):
        self.save_to_undo()
        self.fill(0)
        
    def draw_line(self, p2):
        p1 = self.lastPoint
        # http://fr.wikipedia.org/wiki/Algorithme_de_trac%C3%A9_de_segment_de_Bresenham
        distx = abs(p2.x()-p1.x())
        disty = abs(p2.y()-p1.y())
        if distx > disty:
            step = (p2.y()-p1.y()) / (p2.x()-p1.x() or 1)
            for i in xrange(distx):
                if p1.x() - p2.x() > 0:
                    i = -i
                x = p1.x() + i
                y = int(step * i + p1.y() + 0.5)
                self.draw_point(QtCore.QPoint(x, y))
        else:
            step = (p2.x()-p1.x()) / (p2.y()-p1.y() or 1)
            for i in xrange(disty):
                if p1.y() - p2.y() > 0:
                    i = -i
                y = p1.y() + i
                x = int(step * i + p1.x() + 0.5)
                self.draw_point(QtCore.QPoint(x, y))
        self.draw_point(p2)

    def draw_point(self, point):
        for i, j in self.project.pen:
            p = QtCore.QPoint(point.x()+i, point.y()+j)
            if self.rect().contains(p):
                self.setPixel(p, self.project.color)

    def flood_fill(self, point, col):
        l = [(point.x(), point.y())]
        while l:
            p = l.pop(-1)
            x, y = p[0], p[1]
            if self.rect().contains(x, y) and self.pixelIndex(x, y) == col:
                self.setPixel(QtCore.QPoint(x, y), self.project.color)
                l.append((x+1, y))
                l.append((x-1, y))
                l.append((x, y+1))
                l.append((x, y-1))

    def clic(self, point):
        if ((self.project.tool == "pen" or self.project.tool == "fill") and 
             QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier):
            if self.rect().contains(point):
                self.project.color = self.pixelIndex(point)
                self.project.update_palette.emit()
            self.lastPoint = False
        elif self.project.tool == "pen":
            self.save_to_undo()
            #~ self.project.save_to_undo("canvas")
            if QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier and self.lastPoint:
                self.draw_line(point)
            else:
                self.draw_point(point)
            self.lastPoint = point
        elif self.rect().contains(point):
            col = self.pixelIndex(point)
            if self.project.tool == "pipette":
                self.project.set_color(col)
            elif self.project.tool == "fill" and self.project.color != col:
                self.save_to_undo()
                #~ self.project.save_to_undo("canvas")
                self.flood_fill(point, col)
            self.lastPoint = False

    def move(self, point):
        if ((self.project.tool == "pen" or self.project.tool == "fill") and 
             QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier):
            if self.rect().contains(point):
                self.project.color = self.pixelIndex(point)
                self.project.update_palette.emit()
            self.lastPoint = False
        elif self.project.tool == "pipette":
            if self.rect().contains(point):
                self.project.set_color(self.pixelIndex(point))
            self.lastPoint = False
        elif self.project.tool == "pen":
            if self.lastPoint:
                self.draw_line(point)
                self.lastPoint = point
            else:
                self.draw_point(point)
                self.lastPoint = point

class PaletteCanvas(QtGui.QWidget):
    """ Canvas where the palette is draw """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setFixedSize(164, 324)
        self.background = QtGui.QBrush(QtGui.QColor(150, 150, 150))
        self.alpha = QtGui.QPixmap("icons/color_alpha.png")
        self.black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        self.white = QtGui.QBrush(QtGui.QColor(255, 255, 255))

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

    def mousePressEvent(self, event):
        if (event.button() == QtCore.Qt.LeftButton):
            item = self.item_at(event.x(), event.y())
            if item is not None:
                self.parent.project.set_color(item)

    def mouseDoubleClickEvent(self, event):
        if (event.button() == QtCore.Qt.LeftButton):
            item = self.item_at(event.x(), event.y())
            if item is not None:
                self.parent.edit_color(item)

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
    def __init__(self, project):
        QtGui.QWidget.__init__(self)
        self.project = project
        
        ### tools buttons ###
        self.penB = Button("pen", "icons/tool_pen.png", self.pen_tool_clicked, True)
        self.pipetteB = Button("pipette", "icons/tool_pipette.png", self.pipette_tool_clicked, True)
        self.fillB = Button("fill", "icons/tool_fill.png", self.fill_tool_clicked, True)
        self.moveB = Button("move", "icons/tool_move.png", self.move_tool_clicked, True)
        self.penB.setChecked(True)
        
        ### pen size ###
        self.penW = QtGui.QComboBox(self)
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_1.png")), "point")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_2_hori.png")), "2 pixels horizontal")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_2_vert.png")), "2 pixels vertical")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_2x2_square.png")), "2x2 square")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_3x3_square.png")), "3x3 square")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_3x3_cross.png")), "3x3 cross")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/pen_5x5_round.png")), "5x5 round")
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
                                        (1, 0)),
                        "5x5 round" : ((-1, -2), (0, -2), (1, -2), 
                             (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1), 
                             (-2,  0), (-1,  0), (0,  0), (1,  0), (2,  0), 
                             (-2,  1), (-1,  1), (0,  1), (1,  1), (2,  1), 
                                       (-1,  2), (0,  2), (1,  2))}
        
        ### palette ###
        self.paletteCanvas = PaletteCanvas(self)
        self.project.update_palette.connect(self.paletteCanvas.update)
        addColorB = Button("add color", 
                "icons/color_add.png", self.add_color_clicked)
        delColorB = Button("delete color", 
                "icons/color_del.png", self.del_color_clicked)
        moveLeftColorB = Button("move color left", 
                "icons/color_move_left.png", self.move_color_left_clicked)
        moveRightColorB = Button("move color right", 
                "icons/color_move_right.png", self.move_color_right_clicked)
        
        self.onionSkinPrevB = Button("onion skin - previous frame", 
                "icons/onionskin_prev.png", self.onionskin_prev_clicked, True)
        self.onionSkinNextB = Button("onion skin - next frame", 
                "icons/onionskin_next.png", self.onionskin_next_clicked, True)
        
        ### Layout ###
        layout = QtGui.QGridLayout()
        layout.setSpacing(4)
        layout.addWidget(self.penB, 0, 0)
        layout.addWidget(self.pipetteB, 0, 1)
        layout.addWidget(self.fillB, 0, 2)
        layout.addWidget(self.moveB, 0, 3)
        layout.setColumnStretch(3, 2)
        layout.addWidget(self.penW, 1, 0, 1, 4)
        layout.addWidget(self.paletteCanvas, 2, 0, 1, 4)
        layout.addWidget(addColorB, 3, 0)
        layout.addWidget(delColorB, 3, 1)
        layout.addWidget(moveLeftColorB, 3, 2)
        layout.addWidget(moveRightColorB, 3, 3)
        layout.addWidget(self.onionSkinPrevB, 4, 2)
        layout.addWidget(self.onionSkinNextB, 4, 3)
        self.setLayout(layout)

    def showEvent(self, event):
        self.setFixedWidth(self.width())
        
    ######## Tools #####################################################
    def pen_tool_clicked(self):
        self.project.tool = "pen"
        self.penB.setChecked(True)
        self.pipetteB.setChecked(False)
        self.fillB.setChecked(False)
        self.moveB.setChecked(False)
        self.project.tool_changed.emit()

    def pipette_tool_clicked(self):
        self.project.tool = "pipette"
        self.penB.setChecked(False)
        self.fillB.setChecked(False)
        self.pipetteB.setChecked(True)
        self.moveB.setChecked(False)
        self.project.tool_changed.emit()

    def fill_tool_clicked(self):
        self.project.tool = "fill"
        self.fillB.setChecked(True)
        self.pipetteB.setChecked(False)
        self.penB.setChecked(False)
        self.moveB.setChecked(False)
        self.project.tool_changed.emit()
            
    def move_tool_clicked(self):
        self.project.tool = "move"
        self.fillB.setChecked(False)
        self.pipetteB.setChecked(False)
        self.penB.setChecked(False)
        self.moveB.setChecked(True)
        self.project.tool_changed.emit()

    def pen_chooser_clicked(self, text):
        self.project.pen = self.penDict[str(text)]
        self.project.pen_changed.emit()
    
    ######## Color #####################################################
    def edit_color(self, n):
        col = self.project.colorTable[self.project.color]
        color, ok = QtGui.QColorDialog.getRgba(col)
        if not ok:
            return
        self.project.colorTable[n] = color
        for i in self.project.get_all_canvas():
            i.setColorTable(self.project.colorTable)
        self.project.update_view.emit()
        self.paletteCanvas.update()
        self.project.color_changed.emit()

    def add_color_clicked(self):
        """ select a color and add it to the palette"""
        if not len(self.project.colorTable) >= 128:
            col = self.project.colorTable[self.project.color]
            color, ok = QtGui.QColorDialog.getRgba(col)
            if not ok:
                return
            self.project.colorTable.append(color)
            self.project.set_color(len(self.project.colorTable)-1)
            for i in self.project.get_all_canvas():
                i.setColorTable(self.project.colorTable)
            self.project.update_view.emit()
        
    def del_color_clicked(self):
        col, table = self.project.color, self.project.colorTable
        if col != 0:
            table.pop(col)
            for i in self.project.get_all_canvas():
                i.merge_color(col, 0)
                i.setColorTable(table)
            self.project.set_color(col-1)
            self.project.update_view.emit()
    
    def move_color_left_clicked(self):
        col, table = self.project.color, self.project.colorTable
        if col != 0:
            table[col], table[col-1] = table[col-1], table[col]
            for i in self.project.get_all_canvas():
                i.swap_color(col, col-1)
                i.setColorTable(table)
            self.project.set_color(col-1)
        
    def move_color_right_clicked(self):
        col, table = self.project.color, self.project.colorTable
        if col != len(table)-1:
            table[col], table[col+1] = table[col+1], table[col]
            for i in self.project.get_all_canvas():
                i.swap_color(col, col+1)
                i.setColorTable(table)
            self.project.set_color(col+1)
        
    def onionskin_prev_clicked(self):
        if self.onionSkinPrevB.isChecked():
            self.project.onionSkinPrev = True
        else:
            self.project.onionSkinPrev = False
        self.project.update_view.emit()
        
    def onionskin_next_clicked(self):
        if self.onionSkinNextB.isChecked():
            self.project.onionSkinNext = True
        else:
            self.project.onionSkinNext = False
        self.project.update_view.emit()

class Project(QtCore.QObject):
    """ store all data that need to be saved"""
    update_view = QtCore.pyqtSignal()
    update_palette = QtCore.pyqtSignal()
    update_timeline = QtCore.pyqtSignal()
    pen_changed = QtCore.pyqtSignal()
    tool_changed = QtCore.pyqtSignal()
    color_changed = QtCore.pyqtSignal()
    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.size = DEFAUT_SIZE
        self.colorTable = list(DEFAUT_COLORTABLE)
        self.color = DEFAUT_COLOR
        self.pen = DEFAUT_PEN
        self.tool = DEFAUT_TOOL
        self.frames = [{"frames" : [self.make_canvas(), ], "pos" : 0, "visible" : True, "lock" : False, "name": "Layer 1"},]
        self.fps = 12
        self.currentFrame = 0
        self.currentLayer = 0
        self.playing = False
        self.onionSkinPrev = False
        self.onionSkinNext = False
        
        # TODO
        self.url = None
        self.undoList = []
        self.redoList = []
        
    def set_color(self, color):
        self.color = color
        self.color_changed.emit()
        self.update_palette.emit()
        
        
    ######## undo/redo #################################################
    def save_to_undo(self, obj):
        if obj == "layer":
            pass
        elif obj == "canvas":
            canvas = self.get_canvas()
            self.undoList.append(("canvas", (self.currentFrame, self.currentLayer), Canvas(self, canvas)))
        elif obj == "canvas_size":
            pass
        elif obj == "color":
            pass
            
        if len(self.undoList) > 50:
            self.undoList.pop(0)
        self.redoList = []

    def undo(self):
        if len(self.undoList) > 0:
            toUndo = self.undoList.pop(-1)
            if toUndo[0] == "canvas":
                self.currentFrame = toUndo[1][0]
                self.currentlayer = toUndo[1][1]
                canvas = self.get_canvas()
                self.redoList.append(("canvas", (self.currentFrame, self.currentLayer), Canvas(self, canvas)))
                canvas.swap(toUndo[2])
                
            if len(self.redoList) > 50:
                self.redoList.pop(0)
            self.update_view.emit()
            self.update_timeline.emit()

    def redo(self):
        if len(self.redoList) > 0:
            toRedo = self.redoList.pop(-1)
            if toRedo[0] == "canvas":
                self.currentFrame = toRedo[1][0]
                self.currentlayer = toRedo[1][1]
                canvas = self.get_canvas()
                self.undoList.append(("canvas", (self.currentFrame, self.currentLayer), Canvas(self, canvas)))
                canvas.swap(toRedo[2])
            
            if len(self.undoList) > 50:
                self.undoList.pop(0)
            self.update_view.emit()
            self.update_timeline.emit()
            
    def make_canvas(self, canvas=False):
        """ make a new canvas 
            or a copy of arg:canvas """
        if canvas:
            return Canvas(self, canvas)
        else:
            return Canvas(self, self.size[0], self.size[1])
            
    def make_layer(self, layer=False):
        """ make a new empty layer by default
            or a copy of arg:layer """
        name = "Layer %s" %(len(self.frames)+1)
        if layer:
            l = dict(layer)
            l["name"] = name
            l["frames"] = list(layer["frames"])
            for i,  f in enumerate(l["frames"]):
                if f:
                    l[i] = Canvas(self, f)
            return l
        else:
            return {"frames" : [self.make_canvas(), ], 
                    "pos" : 0, 
                    "visible" : True, 
                    "lock" : False, 
                    "name": name}
        
    def get_canvas_list(self):
        """ return the list of all layer's canvas at self.currentFrame """
        tf = []
        for l in self.frames:
            f = self.currentFrame
            while 0 <= f < len(l["frames"]):
                if l["frames"][f]:
                    tf.append(l["frames"][f])
                    break
                f -= 1
            else:
                tf.append(0)
        return tf
        
    def get_canvas(self, index=False, getIndex=False):
        """ return the current canvas by defaut
            if arg:index, the canvas at (frame, layer)
            if arg:getIndex, the index of canvas in self.frame """
        if index:
            f = index[0]
            l = index[1]
        else:
            f = self.currentFrame
            l = self.currentLayer
        while 0 <= f < len(self.frames[l]["frames"]):
            if self.frames[l]["frames"][f]:
                if getIndex:
                    return (f, l)
                else:
                    return self.frames[l]["frames"][f]
            f -= 1
        return False
        
    def get_prev_canvas(self):
        """ return the previous canvas (if any) for onionskin """
        f = self.get_canvas(False, True)
        l = self.currentLayer
        if f:
            f = f[0]
            for i in reversed(xrange(f)):
                if self.frames[l]["frames"][i]:
                    return self.frames[l]["frames"][i]
        return False
        
    def get_next_canvas(self):
        """ return the next canvas (if any) for onionskin """
        f = self.currentFrame
        l = self.currentLayer
        if f < len(self.frames[l]["frames"]):
            for i in xrange(f+1, len(self.frames[l]["frames"])):
                if self.frames[l]["frames"][i]:
                    return self.frames[l]["frames"][i]
        return False
        
    def get_all_canvas(self):
        """ retrun all canvas from self.frames """
        canvas = []
        for l in self.frames:
            for f in l["frames"]:
                if f:
                    canvas.append(f)
        return canvas
        
class MainWindow(QtGui.QMainWindow):
    """ Main windows of the application """
    currentFrameChanged = QtCore.pyqtSignal(object)
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("pixeditor")

        self.project = Project(self)
        self.toolsWidget = ToolsWidget(self.project)
        self.timeline = Timeline(self.project)
        self.scene = Scene(self.project)

        ### Menu ###
        newAction = QtGui.QAction('&New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.triggered.connect(self.new_action)
        resizeAction = QtGui.QAction('&Resize', self)
        resizeAction.setShortcut('Ctrl+R')
        resizeAction.triggered.connect(self.resize_action)
        importAction = QtGui.QAction('&Open', self)
        importAction.setShortcut('Ctrl+O')
        importAction.triggered.connect(self.open_action)
        saveAction = QtGui.QAction('&Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.save_action)
        exportAction = QtGui.QAction('E&xport', self)
        exportAction.setShortcut('Ctrl+E')
        exportAction.triggered.connect(self.export_action)
        exitAction = QtGui.QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.exit_action)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(newAction)
        fileMenu.addAction(resizeAction)
        fileMenu.addAction(importAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(exportAction)
        fileMenu.addAction(exitAction)

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
        shortcut3 = QtGui.QShortcut(self)
        shortcut3.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Z))
        shortcut3.activated.connect(self.undo)
        shortcut4 = QtGui.QShortcut(self)
        shortcut4.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Y))
        shortcut4.activated.connect(self.redo)

        ### layout #####################################################
        splitter = QtGui.QSplitter()
        splitter.addWidget(self.toolsWidget)
        splitter.addWidget(self.scene)
        splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
        splitter2.addWidget(splitter)
        splitter2.addWidget(self.timeline)
        self.setCentralWidget(splitter2)
        self.show()

    def new_action(self):
        ok, w, h = NewDialog().get_return()
        if ok:
            self.project.color = DEFAUT_COLOR
            self.project.colorTable = list(DEFAUT_COLORTABLE)
            self.project.size = (w, h)
            self.project.frames = [self.project.make_layer()]
            self.project.update_view.emit()
            self.project.update_palette.emit()
            self.project.update_timeline.emit()

    def resize_action(self):
        exSize = self.project.size
        ok, newSize, offset = ResizeDialog(exSize).get_return()
        if ok:
            for y, l in enumerate(self.project.frames):
                for x, f in enumerate(l["frames"]):
                    if f:
                        li = f.return_as_list()
                        nf = Canvas(self.project, newSize[0], newSize[1])
                        nf.load_from_list(li, exSize[0], offset)
                        self.project.frames[y]["frames"][x] = nf
            self.project.size = newSize
            self.project.update_view.emit()

    def open_action(self):
        size, colors, frames = open_pix()
        if size and colors and frames:
            self.project.size = size
            self.project.colorTable = colors
            for y, l in enumerate(frames):
                for x, f in enumerate(l["frames"]):
                    if f:
                        nf = Canvas(self.project, size[0], size[1])
                        nf.load_from_list(f)
                        frames[y]["frames"][x] = nf
            self.project.frames = frames
            self.project.update_view.emit()
            self.project.update_palette.emit()
            self.project.update_timeline.emit()

    def save_action(self):
        save_pix(self.project)

    def export_action(self):
        export(self.project)

    def exit_action(self):
        QtGui.qApp.quit()

    #~ def undo(self):
        #~ self.project.undo()
        #~ self.project.update_view.emit()
        #~ self.project.update_timeline.emit()
#~ 
    #~ def redo(self):
        #~ self.project.redo()
        #~ self.project.update_view.emit()
        #~ self.project.update_timeline.emit()
        
    def undo(self):
        canvas = self.project.get_canvas()
        canvas.undo()
        self.project.update_view.emit()

    def redo(self):
        canvas = self.project.get_canvas()
        canvas.redo()
        self.project.update_view.emit()

    def select_frame(self, n):
        maxF = max([len(l["frames"]) for l in self.project.frames])
        if 0 <= self.project.currentFrame+n < maxF:
            self.project.currentFrame += n
            self.project.update_timeline.emit()
            self.project.update_view.emit()
            
    def select_layer(self, n):
        if 0 <= self.project.currentLayer+n < len(self.project.frames):
            self.project.currentLayer += n
            self.project.update_timeline.emit()
            self.project.update_view.emit()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap("icons/pixeditor.png")))
    mainWin = MainWindow()
    sys.exit(app.exec_())

