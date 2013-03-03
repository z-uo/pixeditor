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


# DONE add play function
# DONE add custom framerate, stop button, repeat
# DONE add still image in timeline > gerer supression
# DONE always one frame selected
# DONE bug when deleting the last frame
# DONE duplicate frame (make a still frame drawable)
# DONE clear frame (create new on a still frame)
# DONE add new canvas / save / open / export
# DONE add palette
# DONE add palette: change color on doubleclic
# DONE add indexed color
# DONE add custom brushes
# DONE add shortcut to change frames
# DONE add undeo redo (work only on canvas)

# DONE add pipette
# DONE add fill
# DONE add resize canvas
# bug save filename
# add more control on palette
# add a tool to make lines (iso...)
# add move frame content
# add icones with update on mouserelese
# add copy paste move frame
# add onionskin
# add layers
# add choice between a gif or png transparency mode
# add a cursor layer (pixel who will be paint) grid
# add animated gif export

from __future__ import division
import sys
import os
import time
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt

from dialogs import *
from import_export import *
from timeline import *

DEFAUT_COLOR = 1
DEFAUT_SIZE = (64, 64)
DEFAUT_COLORTABLE = (QtGui.qRgba(0, 0, 0, 0), QtGui.qRgba(0, 0, 0, 255))
DEFAUT_PEN = ((0, 0),)
DEFAUT_TOOL = "pen"


class Item(QtGui.QStandardItem):
    """ a QStandartItem used in FramesWidget that contain a Canvas """
    def __init__(self, image=None):
        QtGui.QStandardItem.__init__(self)
        self.set_image(image)

    def set_image(self, image=None):
        self.image = image
        if image:
            self.setText('frame')
        else:
            self.setText('   -')
    def get_image(self):
        return self.image


class FramesWidget(QtGui.QWidget):
    """ manages the frames """
    def __init__(self, project, parent):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        self.project = project

        ### model to store images ###
        self.modFramesList = QtGui.QStandardItemModel(0, 1)

        ### listview to display images ###
        self.framesList = QtGui.QTableView()
        self.framesList.setModel(self.modFramesList)
        self.framesList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.framesList.selectionModel().selectionChanged.connect(self.change_frame)
        self.framesList.horizontalHeader().setVisible(False)

        ### adding and deleting images ###
        self.addFrameW = QtGui.QToolButton()
        self.addFrameW.setAutoRaise(True)
        self.addFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_add.png")))
        self.addFrameW.clicked.connect(self.add_frame_clicked)
        self.delFrameW = QtGui.QToolButton()
        self.delFrameW.setAutoRaise(True)
        self.delFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_del.png")))
        self.delFrameW.clicked.connect(self.delete_frame_clicked)
        self.duplicateFrameW = QtGui.QToolButton()
        self.duplicateFrameW.setAutoRaise(True)
        self.duplicateFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_dup.png")))
        self.duplicateFrameW.clicked.connect(self.duplicate_frame_clicked)
        self.eraseFrameW = QtGui.QToolButton()
        self.eraseFrameW.setAutoRaise(True)
        self.eraseFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_clear.png")))
        self.eraseFrameW.clicked.connect(self.clear_frame_clicked)

        # play the animation
        self.playFrameW = QtGui.QToolButton()
        self.playFrameW.state = "play"
        self.playFrameW.setAutoRaise(True)
        self.playFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_play.png")))
        self.playFrameW.clicked.connect(self.play_pause_clicked)
        self.framerate = 1/12
        self.framerateL = QtGui.QLabel("fps")
        self.framerateW = QtGui.QLineEdit(self)
        self.framerateW.setText(str(12))
        self.framerateW.setValidator(QtGui.QIntValidator(self.framerateW))
        self.framerateW.textChanged.connect(self.framerate_changed)

        self.repeatW = QtGui.QToolButton()
        self.repeatW.state = False
        self.repeatW.setAutoRaise(True)
        self.repeatW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_no_repeat.png")))
        self.repeatW.clicked.connect(self.repeat_clicked)

        ### layout ###
        toolBox = QtGui.QHBoxLayout()
        toolBox.addWidget(self.addFrameW)
        toolBox.addWidget(self.delFrameW)
        toolBox.addWidget(self.duplicateFrameW)
        toolBox.addWidget(self.eraseFrameW)
        toolBox.addStretch(0)
        
        toolBox2 = QtGui.QHBoxLayout()
        toolBox2.addWidget(self.framerateW)
        toolBox2.addWidget(self.framerateL)
        toolBox2.addWidget(self.repeatW)
        toolBox2.addWidget(self.playFrameW)
        toolBox2.addStretch(0)
        
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.framesList)
        self.layout.addLayout(toolBox)
        self.layout.addLayout(toolBox2)

    def clear_frames(self):
        for i in xrange(self.modFramesList.rowCount()):
            self.modFramesList.removeRow(0)

    def init_new_anim(self, frames):
        self.clear_frames()
        for i in frames:
            if i:
                img = self.make_frame()
                img.load_from_list(i)
                item = Item(img)
            else:
                item = Item(None)
            self.insert_item(item)
        self.select_frame(0)

    def select_frame(self, row):
        """ select a frame which call self.change_frame() """
        if row < self.modFramesList.rowCount() and row >= 0:
            self.framesList.selectionModel().clear()
            sel = self.modFramesList.createIndex(row,0)
            self.framesList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)

    def select_frame_relative(self, n):
        """ select a frame which call self.change_frame() """
        sel = self.framesList.selectionModel().selectedIndexes()
        if sel:
            self.select_frame(sel[0].row() + n)

    def make_frame(self):
        return Canvas(self.project,
                      self.project.size[0],
                      self.project.size[1],
                      self.project.colorTable)

    def insert_item(self, item):
        """ insert an item after the selection or in the end """
        sel = self.framesList.selectionModel().selectedIndexes()
        if sel:
            row = sel[0].row()+1
        else:
            row = self.modFramesList.rowCount()
        self.modFramesList.insertRow(row, item)
        self.select_frame(row)

    def change_frame(self):
        """ send the selected canvas to the viewer """
        canvas = self.get_canvas()
        if canvas:
            self.parent.currentFrameChanged.emit(canvas)

    def get_canvas(self):
        sel = self.framesList.selectionModel().selectedIndexes()
        if sel:
            item = self.modFramesList.itemFromIndex(sel[0])
            img = item.get_image()
            if not img:
                i = sel[0].row()
                while not img and i >= 0:
                    item = self.modFramesList.item(i,0)
                    img = item.get_image()
                    i -= 1
            return img

    def get_all_canvas(self, still=False):
        """ return a list containing all non still canvas """
        l = []
        for i in xrange(self.modFramesList.rowCount()):
            item = self.modFramesList.item(i,0)
            img = item.get_image()
            if still:
                l.append(img)
            else:
                if img:
                    l.append(img)
        return l
    def get_all_items(self, still=False):
        l = []
        for i in xrange(self.modFramesList.rowCount()):
            item = self.modFramesList.item(i,0)
            if still:
                l.append(item)
            else:
                if item.get_image():
                    l.append(item)
        return l

    def add_frame_clicked(self, qimg=None):
        """ create a new row and a canvas inside """
        # create the canvas and the item hanging it on FramesWidget
        if qimg:
            img = Canvas(self.parent, qimg.copy(0, 0, self.parent.tools["size"][0], self.parent.tools["size"][1]))
        else:
            img = self.make_frame()

        self.insert_item(Item(img))

    def delete_frame_clicked(self):
        """ delete selected frame from the model"""
        sel = self.framesList.selectionModel().selectedIndexes()
        row = sel[0].row()
        self.modFramesList.removeRow(row)
        # if we just deleted the last frame, create a new empty one
        if self.modFramesList.rowCount() == 0:
            self.add_frame_clicked()
        # if we just deleted the first frame,
        #    if the new first frame contain a canvas, select it
        #    else (if its a still frame), create a new empty one
        elif row == 0 :
            item = self.modFramesList.item(0,0)
            if item.get_image():
                self.select_frame(0)
            else:
                item.set_image(self.make_frame())
                self.select_frame(0)
        # else, just select the previous frame
        else:
            self.select_frame(row - 1)

    def duplicate_frame_clicked(self):
        """ duplicate the current canvas or if it's still create one in place """
        sel = self.framesList.selectionModel().selectedIndexes()
        if sel:
            item = self.modFramesList.itemFromIndex(sel[0])
            img = item.get_image()
            if img:
                self.add_frame_clicked(img)
            else:
                sel = sel[0]
                i = 1
                while not img and sel.row()-i >= 0:
                    item = self.modFramesList.item(sel.row()-i, 0)
                    img = item.get_image()
                    i = i + 1
                self.add_frame_clicked(img)

    def clear_frame_clicked(self):
        """ clear the current canvas or if it's still create a blank one """
        sel = self.framesList.selectionModel().selectedIndexes()
        if sel:
            item = self.modFramesList.itemFromIndex(sel[0])
            img = item.get_image()
            if img:
                img.clear()
            else:
                item.set_image(self.make_frame())
        self.change_frame()

    def framerate_changed(self):
        f = int(self.framerateW.text())
        if f:
            self.framerate = 1/f
        else:
            self.framerate = 1

    def repeat_clicked(self):
        if self.repeatW.state:
            self.repeatW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_no_repeat.png")))
            self.repeatW.state = False
        else:
            self.repeatW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_repeat.png")))
            self.repeatW.state = True

    def play_pause_clicked(self):
        """play the animation"""
        if self.playFrameW.state == 'play':
            self.playFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_pause.png")))
            self.playFrameW.state = "stop"
            rows = self.modFramesList.rowCount()
            self.playThread = Play(rows, self)
            self.playThread.frame.connect(self.select_frame)
            self.playThread.end.connect(self.play_end)
            self.playThread.start()
        elif self.playFrameW.state == 'stop':
            self.playThread.stop = True

    def play_end(self):
        self.playFrameW.state = "play"
        self.playFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_play.png")))


class Play(QtCore.QThread):
    """ thread used to play the animation """
    frame = QtCore.pyqtSignal(int)
    end = QtCore.pyqtSignal()
    def __init__(self, rows, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.parent = parent
        self.rows = rows
        self.stop = False

    def run(self):
        if self.parent.repeatW.state:
            while not self.stop and self.parent.repeatW.state:
                self.animate()
        else:
            self.animate()
        self.end.emit()

    def animate(self):
        for i in xrange(self.parent.modFramesList.rowCount()):
            if not self.stop:
                self.frame.emit(i)
                time.sleep(self.parent.framerate)


class Bg(QtGui.QPixmap):
    """ background of the scene"""
    def __init__(self, w, h):
        QtGui.QPixmap.__init__(self, w, h)
        self.brush = QtGui.QBrush(QtGui.QPixmap("icons/bg.png"))
        self.paintEvent()

    def paintEvent(self, ev=None):
        p = QtGui.QPainter(self)
        p.fillRect (0, 0, self.width(), self.height(), self.brush)


class Scene(QtGui.QGraphicsView):
    """ Display, zoom, pan..."""
    def __init__(self, project):
        QtGui.QGraphicsView.__init__(self)
        self.project = project

        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(140, 140, 140)))

        # the canvas to draw on
        self.canvas = False
        self.zoomN = 1

        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.setScene(self.scene)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.setMinimumSize(400, 400)
        #~ self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        w, h = self.project.size[0], self.project.size[1]
        self.scene.setSceneRect(0, 0, w, h)
        self.bg = self.scene.addPixmap(Bg(w, h))
        self.canvasPixmap = QtGui.QPixmap(w, h)
        self.canvasPixmap.fill(QtGui.QColor(0, 0, 0, 0))
        self.canvasItem = self.scene.addPixmap(self.canvasPixmap)

        self.project.currentFrameChanged.connect(self.change_frame)

    def change_frame(self):
        c = self.project.get_canvas()
        if c:
            self.canvas = c
            self.canvasPixmap.convertFromImage(self.canvas)
            self.canvasItem.setPixmap(self.canvasPixmap)

    def change_size(self):
        w, h = self.project.size[0], self.project.size[1]
        self.scene.setSceneRect(0, 0, w, h)
        self.bg.setPixmap(Bg(w, h))

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
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        # pan
        if event.buttons() == QtCore.Qt.MidButton:
            self.startScroll = (self.horizontalScrollBar().value(),
                                self.verticalScrollBar().value())
            self.lastPos = QtCore.QPoint(QtGui.QCursor.pos())
            self.setDragMode(QtGui.QGraphicsView.NoDrag)
        # draw on canvas
        if self.canvas and event.buttons() == QtCore.Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            self.canvas.clic(QtCore.QPoint(int(pos.x()),int(pos.y())))
            self.canvasPixmap.convertFromImage(self.canvas)
            self.canvasItem.setPixmap(self.canvasPixmap)
        else:
            return QtGui.QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        # pan
        if event.buttons() == QtCore.Qt.MidButton:
            globalPos = QtGui.QCursor.pos()
            self.horizontalScrollBar().setValue(self.startScroll[0] -
                    globalPos.x() + self.lastPos.x())
            self.verticalScrollBar().setValue(self.startScroll[1] -
                    globalPos.y() + self.lastPos.y())
        # draw on canvas
        if self.canvas and event.buttons() == QtCore.Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            self.canvas.move(QtCore.QPoint(int(pos.x()),int(pos.y())))
            self.canvasPixmap.convertFromImage(self.canvas)
            self.canvasItem.setPixmap(self.canvasPixmap)
        else:
            return QtGui.QGraphicsView.mouseMoveEvent(self, event)


class Canvas(QtGui.QImage):
    """ Canvas for drawing"""
    def __init__(self, project, w, h=None, col=None):
        self.project = project
        if not h:
            QtGui.QImage.__init__(self, w)
        else:
            QtGui.QImage.__init__(self, w, h, QtGui.QImage.Format_Indexed8)
            self.setColorTable(self.project.colorTable)
            self.fill(0)

        self.lastPoint = QtCore.QPoint(0, 0)
        self.undoList = []
        self.redoList = []

    def load_from_list(self, li, exWidth=None, offset=(0, 0)):
        if not exWidth:
            exWidth = self.width()
        x, y = 0, 0
        for i in li:
            nx, ny = x + offset[0], y + offset[1]
            if self.rect().contains(nx, ny):
                self.setPixel(QtCore.QPoint(nx, ny), i)
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

    def clear(self):
        self.fill(0)

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

    def draw(self, fig, p2):
        self.draw_point(p2)
        if fig == 'line':
            # http://fr.wikipedia.org/wiki/Algorithme_de_trac%C3%A9_de_segment_de_Bresenham
            p1 = self.lastPoint
            if abs(p2.x()-p1.x()) > abs(p2.y()-p1.y()):
                for i in xrange(abs(p1.x()-p2.x())):
                    if p1.x() - p2.x() < 0:
                        x = p1.x() + i
                    else:
                        x = p1.x() - i
                    y = int((p2.y()-p1.y()) / (p2.x()-p1.x()) * (x-p1.x()) + p1.y() + 0.5)
                    self.draw_point(QtCore.QPoint(x, y))
            else:
                for i in xrange(abs(p1.y()-p2.y())):
                    if p1.y() - p2.y() < 0:
                        y = p1.y() + i
                    else:
                        y = p1.y() - i
                    x = int((p2.x()-p1.x()) / (p2.y()-p1.y()) * (y-p1.y()) + p1.x() + 0.5)
                    self.draw_point(QtCore.QPoint(x, y))
        self.lastPoint = p2

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
        if self.project.tool == "pen":
            self.save_to_undo()
            self.draw('point', point)
        elif self.rect().contains(point):
            col = self.pixelIndex(point)
            if self.project.tool == "pipette":
                self.project.select_color(col)
            elif self.project.tool == "fill" and self.project.color != col:
                self.save_to_undo()
                self.flood_fill(point, col)

    def move(self, point):
        if self.project.tool == "pipette":
            if self.rect().contains(point):
                self.project.select_color(self.pixelIndex(point))
        elif self.project.tool == "pen":
            self.draw('line', QtCore.QPoint(point))


class PaletteCanvas(QtGui.QWidget):
    """ Canvas where the palette is draw"""
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setFixedSize(164, 324)
        self.background = QtGui.QBrush(QtGui.QColor(127, 127, 127))
        self.alpha = QtGui.QPixmap("icons/color_alpha.png")

    def paintEvent(self, ev=''):
        p = QtGui.QPainter(self)
        p.fillRect (0, 0, self.width(), self.height(), self.background)
        for n, i in enumerate(self.parent.project.colorTable):
            y = ((n // 8) * 20) + 2
            x = ((n % 8) * 20) + 2
            if n == self.parent.project.color:
                p.fillRect (x, y, 20, 20, QtGui.QBrush(QtGui.QColor(0, 0, 0)))
                p.fillRect (x + 1, y + 1, 18, 18, QtGui.QBrush(QtGui.QColor(255, 255, 255)))
            if i == 0:
                p.drawPixmap(x + 2, y + 2, self.alpha)
            else:
                p.fillRect(x + 2, y + 2, 16, 16, QtGui.QBrush(QtGui.QColor(i)))

    def mousePressEvent(self, event):
        if (event.button() == QtCore.Qt.LeftButton):
            item = self.item_at(event.x(), event.y())
            if item is not None:
                self.parent.project.color = item
                self.update()


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
    """ main windows of the application """
    def __init__(self, project):
        QtGui.QWidget.__init__(self)
        self.project = project
        
        ### tools buttons ###
        self.penB = QtGui.QToolButton()
        self.penB.setAutoRaise(True)
        self.penB.setCheckable(True)
        self.penB.setChecked(True)
        self.penB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/tool_pen.png")))
        self.penB.toggled.connect(self.pen_tool_clicked)
        self.pipetteB = QtGui.QToolButton()
        self.pipetteB.setAutoRaise(True)
        self.pipetteB.setCheckable(True)
        self.pipetteB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/tool_pipette.png")))
        self.pipetteB.toggled.connect(self.pipette_tool_clicked)
        self.fillB = QtGui.QToolButton()
        self.fillB.setAutoRaise(True)
        self.fillB.setCheckable(True)
        self.fillB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/tool_fill.png")))
        self.fillB.toggled.connect(self.fill_tool_clicked)
        self.zoomInB = QtGui.QToolButton()
        self.zoomInB.setAutoRaise(True)
        self.zoomInB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/tool_zoom_in.png")))
        self.zoomInB.clicked.connect(lambda : self.project.parent.scene.scaleView(2))
        self.zoomOutB = QtGui.QToolButton()
        self.zoomOutB.setAutoRaise(True)
        self.zoomOutB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/tool_zoom_out.png")))
        self.zoomOutB.clicked.connect(lambda : self.project.parent.scene.scaleView(0.5))

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
        self.addColorW = QtGui.QToolButton()
        self.addColorW.setAutoRaise(True)
        self.addColorW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/color_add.png")))
        self.addColorW.clicked.connect(self.add_color_clicked)
        
        ### Layout ###
        toolbox = QtGui.QHBoxLayout()
        toolbox.addWidget(self.penB)
        toolbox.addWidget(self.pipetteB)
        toolbox.addWidget(self.fillB)
        toolbox.addWidget(self.zoomInB)
        toolbox.addWidget(self.zoomOutB)
        toolbox.addStretch()
        colorbox = QtGui.QHBoxLayout()
        colorbox.addWidget(self.addColorW)
        colorbox.addStretch(0)
        layout = QtGui.QVBoxLayout()
        layout.addLayout(toolbox)
        layout.addWidget(self.penW)
        layout.addWidget(self.paletteCanvas)
        layout.addLayout(colorbox)
        layout.addStretch()
        self.setLayout(layout)

    ### Tools ##########################################################
    def pen_tool_clicked(self):
        if self.penB.isChecked() or (not self.pipetteB.isChecked() and not self.fillB.isChecked()):
            self.project.tool = "pen"
            self.pipetteB.setChecked(False)
            self.fillB.setChecked(False)
            self.penB.setChecked(True)

    def pipette_tool_clicked(self):
        if self.pipetteB.isChecked() or (not self.penB.isChecked() and not self.fillB.isChecked()):
            self.project.tool = "pipette"
            self.penB.setChecked(False)
            self.fillB.setChecked(False)
            self.pipetteB.setChecked(True)

    def fill_tool_clicked(self):
        if self.fillB.isChecked() or (not self.penB.isChecked() and not self.pipetteB.isChecked()):
            self.project.tool = "fill"
            self.fillB.setChecked(True)
            self.pipetteB.setChecked(False)
            self.penB.setChecked(False)

    def pen_chooser_clicked(self, text):
        self.project.pen = self.penDict[str(text)]
    
    ### Color ##########################################################
    def change_canvas_colortable(self):
        """ change the color for all canvas """
        for i in self.project.get_all_canvas():
            i.setColorTable(self.project.colorTable)
        self.project.currentFrameChanged.emit()

    def edit_color(self, n):
        col = self.project.colorTable[self.project.color]
        color, ok = QtGui.QColorDialog.getRgba(col)
        if not ok:
            return
        self.project.colorTable[n] = color
        self.paletteCanvas.update()
        self.change_canvas_colortable()

    def add_color_clicked(self):
        """ select a color in a qcolordialog and add it to the palette"""
        if not len(self.project.colorTable) >= 128:
            col = self.project.colorTable[project.color]
            color, ok = QtGui.QColorDialog.getRgba(col)
            if not ok:
                return
            self.project.colorTable.append(color)
            self.project.color = len(self.project.colorTable) -1
            self.paletteCanvas.update()
            self.change_canvas_colortable()

    def select_color(self, n):
        self.project.color = n
        self.paletteCanvas.update()


class Project(QtCore.QObject):
    """ store all data that need to be saved"""
    currentFrameChanged = QtCore.pyqtSignal()
    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.size = DEFAUT_SIZE
        self.colorTable = list(DEFAUT_COLORTABLE)
        self.color = DEFAUT_COLOR
        self.pen = DEFAUT_PEN
        self.tool = DEFAUT_TOOL
        self.frames = [{"frames" : [self.make_canvas(), ], "name": "Layer 01"},]
        self.fps = 12
        self.currentFrame = 0
        self.currentLayer = 0
        
        # TODO
        self.url = None
        
    def make_canvas(self):
        return Canvas(self, self.size[0], self.size[1], self.colorTable)
        
    def select_color(self, i):
        pass
        
    def get_canvas(self):
        f = self.currentFrame
        while 0 <= f < len(self.frames[0]["frames"]):
            if self.frames[0]["frames"][f]:
                return self.frames[0]["frames"][f]
            f -= 1
        return False
            
    def get_all_canvas(self):
        pass
        
        
class MainWindow(QtGui.QMainWindow):
    currentFrameChanged = QtCore.pyqtSignal(object)
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("pixeditor")

        self.project = Project(self)

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
        oldImportAction = QtGui.QAction('Open old pix', self)
        oldImportAction.triggered.connect(self.open_old_action)
        saveAction = QtGui.QAction('&Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.save_action)
        exportAction = QtGui.QAction('&export', self)
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
        fileMenu.addAction(oldImportAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(exportAction)
        fileMenu.addAction(exitAction)

        ### shortcuts ###
        shortcut = QtGui.QShortcut(self)
        shortcut.setKey(QtCore.Qt.Key_Left)
        shortcut.activated.connect(lambda : self.framesWidget.select_frame_relative(-1))
        shortcut2 = QtGui.QShortcut(self)
        shortcut2.setKey(QtCore.Qt.Key_Right)
        shortcut2.activated.connect(lambda : self.framesWidget.select_frame_relative(1))
        shortcut3 = QtGui.QShortcut(self)
        shortcut3.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Z))
        shortcut3.activated.connect(self.undo)
        shortcut4 = QtGui.QShortcut(self)
        shortcut4.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Y))
        shortcut4.activated.connect(self.redo)

        ### palette ###
        self.toolsWidget = ToolsWidget(self.project)

        ### viewer and framesWidget ###
        self.framesWidget = FramesWidget(self.project, self)
        self.timeline = Timeline(self.project)
        self.scene = Scene(self.project)

        ### layout #####################################################
        splitter = QtGui.QSplitter()
        splitter.addWidget(self.toolsWidget)
        splitter.addWidget(self.scene)
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(splitter)
        layout.addWidget(self.timeline)

        ### central widget ###
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(layout)
        self.setCentralWidget(self.centralWidget)
        self.init_canvas()
        self.show()

    def init_canvas(self):
        self.scene.change_size()
        # create the first frame
        self.framesWidget.add_frame_clicked()
        # and select it
        sel = self.framesWidget.modFramesList.createIndex(0, 0)
        self.framesWidget.framesList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)

    def new_action(self):
        ok, w, h = NewDialog().get_return()
        if ok:
            self.framesWidget.clear_frames()
            self.project.color = DEFAUT_COLOR
            self.project.colorTable = list(DEFAUT_COLORTABLE)
            self.project.size = (w, h)
            self.palette.paletteCanvas.update()
            self.init_canvas()

    def resize_action(self):
        exSize = self.tools["size"]
        ok, newSize, offset = ResizeDialog(exSize).get_return()
        if ok:
            items = self.framesWidget.get_all_items()
            for i in items:
                canvas = i.get_image()
                l = canvas.return_as_list()
                ncanvas = Canvas(self, newSize[0], newSize[1])
                ncanvas.load_from_list(l, exSize[0], offset)
                i.set_image(ncanvas)
            self.tools["size"] = newSize
            self.scene.change_size()
            self.framesWidget.change_frame()

    def open_action(self):
        size, colors, frames = open_pix()
        if size and colors and frames:
            self.tools["size"] = (size[0], size[1])
            self.tools["colortable"] = colors
            self.palette.paletteCanvas.update()
            self.framesWidget.init_new_anim(frames)
            
    def open_old_action(self):
        size, colors, frames = open_old_pix()
        if size and colors and frames:
            self.tools["size"] = (size[0], size[1])
            self.tools["colortable"] = colors
            self.palette.paletteCanvas.update()
            self.framesWidget.init_new_anim(frames)

    def save_action(self):
        save_pix(self.tools["size"],
                 self.tools["colortable"],
                 self.framesWidget.get_all_canvas(True))

    def export_action(self):
        export(self.framesWidget.get_all_canvas(True))

    def exit_action(self):
        QtGui.qApp.quit()

    def undo(self):
        canvas = self.framesWidget.get_canvas()
        canvas.undo()
        self.scene.change_frame(canvas)

    def redo(self):
        canvas = self.framesWidget.get_canvas()
        canvas.redo()
        self.scene.change_frame(canvas)

    def change_frame(self, pixmap):
        self.scene.setCanvas(pixmap)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainWin = MainWindow()
    sys.exit(app.exec_())

