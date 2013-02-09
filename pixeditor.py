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
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

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
        self.addFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/add.png")))
        self.addFrameW.clicked.connect(self.add_frame_clicked)
        self.stillFrameW = QtGui.QToolButton()
        self.stillFrameW.setAutoRaise(True)
        self.stillFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/still.png")))
        self.stillFrameW.clicked.connect(self.still_frame_clicked)
        self.delFrameW = QtGui.QToolButton()
        self.delFrameW.setAutoRaise(True)
        self.delFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/delete.png")))
        self.delFrameW.clicked.connect(self.delete_frame_clicked)
        self.duplicateFrameW = QtGui.QToolButton()
        self.duplicateFrameW.setAutoRaise(True)
        self.duplicateFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/duplicate.png")))
        self.duplicateFrameW.clicked.connect(self.duplicate_frame_clicked)
        self.eraseFrameW = QtGui.QToolButton()
        self.eraseFrameW.setAutoRaise(True)
        self.eraseFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/clear.png")))
        self.eraseFrameW.clicked.connect(self.clear_frame_clicked)

        # play the animation
        self.playFrameW = QtGui.QToolButton()
        self.playFrameW.state = "play"
        self.playFrameW.setAutoRaise(True)
        self.playFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play.png")))
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
        self.repeatW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/no_repeat.png")))
        self.repeatW.clicked.connect(self.repeat_clicked)

        ### layout ###
        toolBox = QtGui.QHBoxLayout()
        toolBox.addWidget(self.addFrameW)
        toolBox.addWidget(self.stillFrameW)
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
        return Canvas(self.parent,
                       self.parent.tools["size"][0],
                       self.parent.tools["size"][1],
                       self.parent.tools["colortable"])

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

    def still_frame_clicked(self):
        """ add a still frame after the current """
        self.insert_item(Item())

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
                    item = self.modFramesList.item(sel.row()-i,0)
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
            self.repeatW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/no_repeat.png")))
            self.repeatW.state = False
        else:
            self.repeatW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/repeat.png")))
            self.repeatW.state = True

    def play_pause_clicked(self):
        """play the animatio since the selected frame"""
        if self.playFrameW.state == 'play':
            self.playFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/pause.png")))
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
        self.playFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play.png")))


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
    def __init__(self, parent):
        QtGui.QGraphicsView.__init__(self)
        self.parent = parent

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

        w, h = self.parent.tools["size"][0], self.parent.tools["size"][1]
        self.scene.setSceneRect(0, 0, w, h)
        self.bg = self.scene.addPixmap(Bg(w, h))
        self.canvasPixmap = QtGui.QPixmap(w, h)
        self.canvasPixmap.fill(QtGui.QColor(0, 0, 0, 0))
        self.canvasItem = self.scene.addPixmap(self.canvasPixmap)

        self.parent.currentFrameChanged.connect(self.change_frame)

    def change_frame(self, canvas):
        self.canvas = canvas
        self.canvasPixmap.convertFromImage(self.canvas)
        self.canvasItem.setPixmap(self.canvasPixmap)

    def change_size(self):
        w, h = self.parent.tools["size"][0], self.parent.tools["size"][1]
        self.scene.setSceneRect(0, 0, w, h)
        self.bg.setPixmap(Bg(w, h))

    def wheelEvent(self, event):
        if event.delta() > 0:
            self.scaleView(2)
        elif event.delta() < 0:
            self.scaleView(0.5)

    def scaleView(self, factor):
        n = self.zoomN * factor
        if n < 1 or n > 16:
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
            self.canvas.clic(int(pos.x()), int(pos.y()))
            self.canvasPixmap.convertFromImage(self.canvas)
            self.canvasItem.setPixmap(self.canvasPixmap)
        else:
            return QtGui.QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        # pan
        if event.buttons() == QtCore.Qt.MidButton:
            globalPos = QtGui.QCursor.pos()
            self.horizontalScrollBar().setValue(self.startScroll[0] -
                                                globalPos.x() +
                                                self.lastPos.x())
            self.verticalScrollBar().setValue(self.startScroll[1] -
                                              globalPos.y() +
                                              self.lastPos.y())
        # draw on canvas
        if self.canvas and event.buttons() == QtCore.Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            self.canvas.move(int(pos.x()), int(pos.y()))
            self.canvasPixmap.convertFromImage(self.canvas)
            self.canvasItem.setPixmap(self.canvasPixmap)
        else:
            return QtGui.QGraphicsView.mouseMoveEvent(self, event)


class Canvas(QtGui.QImage):
    """ Canvas for drawing"""
    def __init__(self, parent, w, h=None, col=None):
        self.parent = parent
        if not h:
            QtGui.QImage.__init__(self, w)
        else:
            QtGui.QImage.__init__(self, w, h, QtGui.QImage.Format_Indexed8)
            self.setColorTable(self.parent.tools["colortable"])
            self.fill(0)

        self.lastPoint = QtCore.QPoint(0,0)
        self.undoList = []
        self.redoList = []

    def load_from_list(self, li):
        x, y = 0, 0
        for i in li:
            self.setPixel(QtCore.QPoint(x, y), i)
            x += 1
            if x >= self.width():
                x = 0
                y += 1

    def load_from_list_with_offset(self, li, oriW, offset):
        x, y = 0, 0
        for i in li:
            nx, ny = x + offset[0], y + offset[1]
            if nx >= 0 and nx < self.width() and ny >= 0 and ny < self.height():
                self.setPixel(QtCore.QPoint(nx, ny), i)
            x += 1
            if x >= oriW:
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

    def undo(self):
        if len(self.undoList) > 0:
            self.redoList.append(Canvas(self.parent, self))
            if len(self.redoList) > 50:
                self.redoList.pop(0)
            self.swap(self.undoList.pop(-1))

    def redo(self):
        if len(self.redoList) > 0:
            self.undoList.append(Canvas(self.parent, self))
            if len(self.undoList) > 50:
                self.undoList.pop(0)
            self.swap(self.redoList.pop(-1))

    def draw(self, fig, p2):
        if fig == 'point':
            self.draw_point(p2)
        else:
            # http://fr.wikipedia.org/wiki/Algorithme_de_trac%C3%A9_de_segment_de_Bresenham
            p1 = self.lastPoint
            if abs(p2.x()-p1.x()) > abs(p2.y()-p1.y()):
                for i in xrange(abs(p1.x()-p2.x())):
                    if p1.x()-p2.x() < 0:
                        x = p1.x() + i
                    else:
                        x = p1.x() - i
                    y = int( (p2.y()-p1.y()) / (p2.x() - p1.x()) * (x - p1.x()) + p1.y() + 0.5)
                    self.draw_point(QtCore.QPoint(x, y))
                self.draw_point(p2)
            else:
                for i in xrange(abs(p1.y()-p2.y())):
                    if p1.y()-p2.y() < 0:
                        y = p1.y() + i
                    else:
                        y = p1.y() - i
                    x = int( (p2.x()-p1.x()) / (p2.y() - p1.y()) * (y - p1.y()) + p1.x() + 0.5)
                    self.draw_point(QtCore.QPoint(x, y))
                self.draw_point(p2)
        self.lastPoint = p2

    def draw_point(self, point):
        for i in self.parent.tools["pen"]:
            x, y = point.x() + i[0], point.y() + i[1]
            if x >= 0 and x < self.width() and y >= 0 and y < self.height():
                self.setPixel(QtCore.QPoint(x, y), self.parent.tools["color"])

    def flood_fill(self, x, y, col):
        l = [(x, y)]
        while l:
            p = l.pop(0)
            x, y = p[0], p[1]
            if     (x >= 0 and x < self.width() and
                    y >= 0 and y < self.height() and
                    self.pixelIndex(x, y) == col):
                self.setPixel(QtCore.QPoint(x, y), self.parent.tools["color"])
                l.append((x+1, y))
                l.append((x-1, y))
                l.append((x, y+1))
                l.append((x, y-1))

    def save_to_undo(self):
        self.undoList.append(Canvas(self.parent, self))
        if len(self.undoList) > 50:
            self.undoList.pop(0)
        self.redoList = []

    def clic(self, x, y):
        if self.parent.tools["tool"] == "pipette":
            if x >= 0 and x < self.width() and y >= 0 and y < self.height():
                self.parent.palette.select_color(self.pixelIndex(x, y))
        elif self.parent.tools["tool"] == "pen":
            self.save_to_undo()
            self.draw('point', QtCore.QPoint(x, y))
        elif self.parent.tools["tool"] == "fill":
            if     (x >= 0 and x < self.width() and y >= 0 and y < self.height() and
                    self.parent.tools["color"] != self.pixelIndex(x, y)):
                self.save_to_undo()
                self.flood_fill(x, y, self.pixelIndex(x, y))

    def move(self, x, y):
        if self.parent.tools["tool"] == "pipette":
            if x >= 0 and x < self.width() and y >= 0 and y < self.height():
                self.parent.palette.select_color(self.pixelIndex(x, y))
        elif self.parent.tools["tool"] == "pen":
            self.draw('line', QtCore.QPoint(x, y))


class PaletteCanvas(QtGui.QWidget):
    """ Canvas where the palette is draw"""
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setFixedSize(164, 324)
        self.background = QtGui.QBrush(QtGui.QColor(127, 127, 127))
        self.alpha = QtGui.QPixmap("icons/alpha.png")

    def paintEvent(self, ev=''):
        p = QtGui.QPainter(self)
        p.fillRect (0, 0, self.width(), self.height(), self.background)
        for n, i in enumerate(self.parent.parent.tools["colortable"]):
            y = ((n // 8) * 20) + 2
            x = ((n % 8) * 20) + 2
            if n == self.parent.parent.tools["color"]:
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
                self.parent.parent.tools["color"] = item
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
            if s >= 0 and s < len(self.parent.parent.tools["colortable"]):
                return s
            return None


class PaletteWidget(QtGui.QWidget):
    """ main windows of the application """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent

        ### viewer ###
        self.paletteCanvas = PaletteCanvas(self)

        ### adding and deleting color ###
        self.addColorW = QtGui.QToolButton()
        self.addColorW.setAutoRaise(True)
        self.addColorW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/add_color.png")))
        self.addColorW.clicked.connect(self.add_color_clicked)
        ### layout ###
        toolbox = QtGui.QHBoxLayout()
        toolbox.addWidget(self.addColorW)
        toolbox.addStretch(0)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.paletteCanvas)
        layout.addLayout(toolbox)
        self.setLayout(layout)

    def change_canvas_colortable(self):
        """ change the color for all canvas """
        for i in self.parent.framesWidget.get_all_canvas():
            i.setColorTable(self.parent.tools["colortable"])
        # update canvas
        canvas = self.parent.framesWidget.get_canvas()
        self.parent.currentFrameChanged.emit(canvas)

    def edit_color(self, n):
        col = self.parent.tools["colortable"][self.parent.tools["color"]]
        color, ok = QtGui.QColorDialog.getRgba(col)
        if not ok:
            return
        self.parent.tools["colortable"][n] = color
        self.paletteCanvas.update()
        self.change_canvas_colortable()

    def add_color_clicked(self):
        """ select a color in a qcolordialog and add it to the palette"""
        if not len(self.parent.tools["colortable"]) >= 128:
            col = self.parent.tools["colortable"][self.parent.tools["color"]]
            color, ok = QtGui.QColorDialog.getRgba(col)
            if not ok:
                return
            self.parent.tools["colortable"].append(color)
            self.parent.tools["color"] = len(self.parent.tools["colortable"]) -1
            self.paletteCanvas.update()
            self.change_canvas_colortable()

    def select_color(self, n):
        self.parent.tools["color"] = n
        self.paletteCanvas.update()

class MainWidget(QtGui.QWidget):
    currentFrameChanged = QtCore.pyqtSignal(object)
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.tools = {"color" : DEFAUT_COLOR,
                      "size" : DEFAUT_SIZE,
                      "colortable" : list(DEFAUT_COLORTABLE),
                      "pen" : DEFAUT_PEN,
                      "tool" : DEFAUT_TOOL}

        self.state = {"playing" : False,
                      "saved" : False}

        ### buttons ###
        self.penB = QtGui.QToolButton()
        self.penB.setAutoRaise(True)
        self.penB.setCheckable(True)
        self.penB.setChecked(True)
        self.penB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/pen.png")))
        self.penB.toggled.connect(self.pen_tool_clicked)
        self.pipetteB = QtGui.QToolButton()
        self.pipetteB.setAutoRaise(True)
        self.pipetteB.setCheckable(True)
        self.pipetteB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/pipette.png")))
        self.pipetteB.toggled.connect(self.pipette_tool_clicked)
        self.fillB = QtGui.QToolButton()
        self.fillB.setAutoRaise(True)
        self.fillB.setCheckable(True)
        self.fillB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/fill.png")))
        self.fillB.toggled.connect(self.fill_tool_clicked)
        self.zoomInB = QtGui.QToolButton()
        self.zoomInB.setAutoRaise(True)
        self.zoomInB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/zoom_in.png")))
        self.zoomInB.clicked.connect(self.zoom_in)
        self.zoomOutB = QtGui.QToolButton()
        self.zoomOutB.setAutoRaise(True)
        self.zoomOutB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/zoom_out.png")))
        self.zoomOutB.clicked.connect(self.zoom_out)

        ### pen size ###
        self.penW = QtGui.QComboBox(self)
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/point.png")), "point")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/2_pixels_horizontal.png")), "2 pixels horizontal")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/2_pixels_vertical.png")), "2 pixels vertical")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/2x2_square.png")), "2x2 square")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/3x3_square.png")), "3x3 square")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/3x3_cross.png")), "3x3 cross")
        self.penW.addItem(QtGui.QIcon(QtGui.QPixmap("icons/5x5_round.png")), "5x5 round")
        self.penW.activated[str].connect(self.pen_chooser_clicked)
        self.penDict = { "point" : ((0, 0),),
                        "2 pixels horizontal" : ((0, 0), (1, 0)),
                        "2 pixels vertical" : ((0, 0), (0, 1)),
                        "2x2 square" : ((0, 0), (0, 1), (1, 0), (1, 1)),
                        "3x3 square" : ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 0), (0, 1), (1, -1), (1, 0), (1, 1)),
                        "3x3 cross" : ((0, 0), (-1, 0), (0, -1), (1, 0), (0, 1)),
                        "5x5 round" : ((-1, -2), (0, -2), (1, -2), (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (-1, 2), (0, 2), (1, 2))}
        ### palette ###
        self.palette = PaletteWidget(self)

        ### viewer and framesWidget ###
        self.framesWidget = FramesWidget(self)
        self.scene = Scene(self)

        ### layout #####################################################
        zoombox = QtGui.QHBoxLayout()
        zoombox.addWidget(self.penB)
        zoombox.addWidget(self.pipetteB)
        zoombox.addWidget(self.fillB)
        zoombox.addWidget(self.zoomInB)
        zoombox.addWidget(self.zoomOutB)
        zoombox.addStretch()
        toolbox = QtGui.QVBoxLayout()
        toolbox.addLayout(zoombox)
        toolbox.addWidget(self.penW)
        toolbox.addWidget(self.palette)
        toolbox.addStretch()
        splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.framesWidget)
        splitter.addWidget(self.scene)

        layout = QtGui.QHBoxLayout()
        layout.setSpacing(2)
        layout.addLayout(toolbox)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def zoom_in(self):
        self.scene.scaleView(2)

    def zoom_out(self):
        self.scene.scaleView(0.5)

    def pen_tool_clicked(self):
        if self.penB.isChecked() or (not self.pipetteB.isChecked() and not self.fillB.isChecked()):
            self.tools["tool"] = "pen"
            self.pipetteB.setChecked(False)
            self.fillB.setChecked(False)
            self.penB.setChecked(True)

    def pipette_tool_clicked(self):
        if self.pipetteB.isChecked() or (not self.penB.isChecked() and not self.fillB.isChecked()):
            self.tools["tool"] = "pipette"
            self.penB.setChecked(False)
            self.fillB.setChecked(False)
            self.pipetteB.setChecked(True)

    def fill_tool_clicked(self):
        if self.fillB.isChecked() or (not self.penB.isChecked() and not self.pipetteB.isChecked()):
            self.tools["tool"] = "fill"
            self.fillB.setChecked(True)
            self.pipetteB.setChecked(False)
            self.penB.setChecked(False)

    def pen_chooser_clicked(self, text):
        self.tools["pen"] = self.penDict[str(text)]

    def change_frame(self, pixmap):
        self.scene.setCanvas(pixmap)


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("pixeditor")

        ### Menu ###
        # new
        newAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.setStatusTip('New canvas')
        newAction.triggered.connect(self.new_action)
        # resize
        resizeAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Resize', self)
        resizeAction.setShortcut('Ctrl+R')
        resizeAction.setStatusTip('Resize canvas')
        resizeAction.triggered.connect(self.resize_action)
        # open
        importAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Open', self)
        importAction.setShortcut('Ctrl+O')
        importAction.setStatusTip('Open animation')
        importAction.triggered.connect(self.open_action)
        # save
        saveAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save animation')
        saveAction.triggered.connect(self.save_action)
        # export
        exportAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&export', self)
        exportAction.setShortcut('Ctrl+E')
        exportAction.setStatusTip('Export animation')
        exportAction.triggered.connect(self.export_action)
        # exit
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exit_action)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(newAction)
        fileMenu.addAction(resizeAction)
        fileMenu.addAction(importAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(exportAction)
        fileMenu.addAction(exitAction)

        ### central widget ###
        self.centralWidget = MainWidget()
        self.setCentralWidget(self.centralWidget)
        self.init_canvas()

        ### shortcuts ###
        shortcut = QtGui.QShortcut(self)
        shortcut.setKey(QtCore.Qt.Key_Left)
        shortcut.activated.connect(self.previous_frame)
        shortcut2 = QtGui.QShortcut(self)
        shortcut2.setKey(QtCore.Qt.Key_Right)
        shortcut2.activated.connect(self.next_frame)
        shortcut3 = QtGui.QShortcut(self)
        shortcut3.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Z))
        shortcut3.activated.connect(self.undo)
        shortcut4 = QtGui.QShortcut(self)
        shortcut4.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Y))
        shortcut4.activated.connect(self.redo)
        self.show()

    def init_canvas(self):
        self.centralWidget.scene.change_size()
        # create the first frame
        self.centralWidget.framesWidget.add_frame_clicked()
        # and select it
        sel = self.centralWidget.framesWidget.modFramesList.createIndex(0,0)
        self.centralWidget.framesWidget.framesList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)

    def new_action(self):
        ok, w, h = NewDialog().get_return()
        if ok:
            self.centralWidget.framesWidget.clear_frames()
            self.centralWidget.tools["color"] = DEFAUT_COLOR
            self.centralWidget.tools["colortable"] = list(DEFAUT_COLORTABLE)
            self.centralWidget.tools["size"] = (w, h)
            self.centralWidget.palette.paletteCanvas.update()
            self.init_canvas()

    def resize_action(self):
        exSize = self.centralWidget.tools["size"]
        ok, newSize, offset = ResizeDialog(exSize).get_return()
        if ok:
            items = self.centralWidget.framesWidget.get_all_items()
            for i in items:
                canvas = i.get_image()
                l = canvas.return_as_list()
                ncanvas = Canvas(self.centralWidget, newSize[0], newSize[1])
                ncanvas.load_from_list_with_offset(l, exSize[0], offset)
                i.set_image(ncanvas)
            self.centralWidget.tools["size"] = newSize
            self.centralWidget.scene.change_size()
            self.centralWidget.framesWidget.change_frame()

    def open_action(self):
        size, colors, frames = open_pix()
        if size and colors and frames:
            self.centralWidget.tools["size"] = (size[0], size[1])
            self.centralWidget.tools["colortable"] = colors
            self.centralWidget.palette.paletteCanvas.update()
            self.centralWidget.framesWidget.init_new_anim(frames)

    def save_action(self):
        save_pix(self.centralWidget.tools["size"],
                 self.centralWidget.tools["colortable"],
                 self.centralWidget.framesWidget.get_all_canvas(True))

    def export_action(self):
        export(self.centralWidget.framesWidget.get_all_canvas(True))

    def exit_action(self):
        QtGui.qApp.quit()

    def previous_frame(self):
        self.centralWidget.framesWidget.select_frame_relative(-1)

    def next_frame(self):
        self.centralWidget.framesWidget.select_frame_relative(1)

    def undo(self):
        canvas = self.centralWidget.framesWidget.get_canvas()
        canvas.undo()
        self.centralWidget.scene.change_frame(canvas)

    def redo(self):
        canvas = self.centralWidget.framesWidget.get_canvas()
        canvas.redo()
        self.centralWidget.scene.change_frame(canvas)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainWin = MainWindow()
    sys.exit(app.exec_())

