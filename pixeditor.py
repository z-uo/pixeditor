#!/usr/bin/env python
#-*- coding: utf-8 -*-

from __future__ import division
import sys
import os
import time
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt

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
# add custom brushes
# manage thread if we add or remove images or lock interface while playing
# need UI love

# later 
# add resize canvas
# add move frame content
# maybe add play from here, foreward/backward repeat, play backward > advanced control
# add icones with update on mouserelese
# add copy paste move frame
# add onionskin
# add layers
# add choice between a gif or png transparency mode

### global ###
# drawing color
COLOR = 1
# canvas size
SIZE = (64, 64)
COLORTABLE = [QtGui.qRgba(0, 0, 0, 0), QtGui.qRgba(0, 0, 0, 255)]


class Item(QtGui.QStandardItem):
    """ a QStandartItem that contain a Canvas """
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
        #
        #~ # try to make an icon
        #~ self.framesList.setIconSize(QtCore.QSize(32, 32))
        #~ # try to move frame by drag drop
        #~ self.framesList.setDefaultDropAction(QtCore.Qt.MoveAction)
        #~ self.framesList.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        
        ### adding and deleting images ###
        self.addFrameW = QtGui.QPushButton('add')
        self.addFrameW.clicked.connect(self.add_frame_clicked)
        self.stillFrameW = QtGui.QPushButton('still')
        self.stillFrameW.clicked.connect(self.still_frame_clicked)
        self.delFrameW = QtGui.QPushButton('delete')
        self.delFrameW.clicked.connect(self.delete_frame_clicked)
        self.duplicateFrameW = QtGui.QPushButton('duplicate')
        self.duplicateFrameW.clicked.connect(self.duplicate_frame_clicked)
        self.eraseFrameW = QtGui.QPushButton('clear')
        self.eraseFrameW.clicked.connect(self.clear_frame_clicked)
        
        # play the animation
        self.playFrameW = QtGui.QPushButton('play')
        self.playFrameW.clicked.connect(self.play_pause_clicked)
        self.framerate = 1/12
        self.framerateL = QtGui.QLabel("fps")
        self.framerateW = QtGui.QLineEdit(self)
        self.framerateW.setText(str(12))
        self.framerateW.setValidator(QtGui.QIntValidator(self.framerateW))
        self.framerateW.textChanged.connect(self.framerate_changed)
        
        self.repeat = False
        self.checkRepeatW = QtGui.QCheckBox("repeat")
        self.checkRepeatW.clicked.connect(self.check_repeat)

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
        toolBox2.addWidget(self.checkRepeatW)
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
                img = Canvas(SIZE[0], SIZE[1])
                img.load_from_list(i)
                item = Item(img)
            else:
                item = Item(None)
            self.insert_item(item)
        self.select_frame(0)
                
    def select_frame(self, row):
        """ select a frame which call self.change_frame() """
        self.framesList.selectionModel().clear()
        sel = self.modFramesList.createIndex(row,0)
        self.framesList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)
        
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
                
    def add_frame_clicked(self, qimg=None):
        """ create a new row and a canvas inside """
        # create the canvas and the item haning it on FramesWidget
        if qimg:
            img = Canvas(qimg.copy(0, 0, SIZE[0], SIZE[1]))
        else:
            img = Canvas(SIZE[0], SIZE[1])
            
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
                img = Canvas(SIZE[0], SIZE[1])
                item.set_image(img)
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
                img = Canvas(SIZE[0], SIZE[1])
                item.set_image(img)
        self.change_frame()
        
    def framerate_changed(self):
        f = int(self.framerateW.text())
        if f:
            self.framerate = 1/f
        else:
            self.framerate = 1
        
    def check_repeat(self):
        if self.checkRepeatW.isChecked():
            self.repeat = True
        else:
            self.repeat = False
        
    def play_pause_clicked(self):
        """play the animatio since the selected frame"""
        if self.playFrameW.text() == 'play':
            self.playFrameW.setText('stop')
            rows = self.modFramesList.rowCount()
            self.playThread = Play(rows, self)
            self.playThread.frame.connect(self.select_frame)
            self.playThread.end.connect(self.play_end)
            self.playThread.start()
        elif self.playFrameW.text() == 'stop':
            self.playThread.stop = True
            
    def play_end(self):
        self.playFrameW.setText('play') 
        

class Play(QtCore.QThread):
    """ thread used to apply the code on images
    """
    frame = QtCore.pyqtSignal(int)
    end = QtCore.pyqtSignal()
    def __init__(self, rows, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.parent = parent
        self.rows = rows
        self.stop = False

    def run(self):
        if self.parent.repeat:
            while not self.stop and self.parent.repeat:
                self.animate()
        else:
            self.animate()
        self.end.emit()
            
    def animate(self):
        for i in xrange(self.parent.modFramesList.rowCount()):
            if not self.stop:
                self.frame.emit(i)
                time.sleep(self.parent.framerate)
        

class ColorItem(QtGui.QStandardItem):
    """ a QStandartItem that contain a Color """
    def __init__(self, color):
        QtGui.QStandardItem.__init__(self)
        self.setEditable(False)
        self.color = color
        self.add_icon()
        
    def set_color(self, color):
        self.color = color
        self.add_icon()
    def get_color(self):
        return self.color
        
    def add_icon(self):
        col = QtGui.QColor()
        col.setRgba(self.color)
        if col.alpha() == 0:
            icon = QtGui.QPixmap("icons/alpha.png")
        else:
            icon = QtGui.QPixmap(16,16)
            icon.fill(col)
        self.setIcon(QtGui.QIcon(icon))
        
        
class Palette(QtGui.QWidget):
    """ color palette """
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        
        ### model to store palette ###
        self.modColorList = QtGui.QStandardItemModel(0, 1)

        ### listview to display palette ###
        self.colorList = QtGui.QListView()
        self.colorList.setModel(self.modColorList)
        self.colorList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.colorList.selectionModel().selectionChanged.connect(self.change_color)
        self.colorList.doubleClicked.connect(self.edit_color)
        
        ### adding and deleting color ###
        self.addColorW = QtGui.QPushButton('add')
        self.addColorW.clicked.connect(self.add_color_clicked)

        ### layout ###
        toolBox = QtGui.QHBoxLayout()
        toolBox.addWidget(self.addColorW)
        toolBox.addStretch(0)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.colorList)
        self.layout.addLayout(toolBox)
    
    def clear_palette(self):
        for i in xrange(self.modColorList.rowCount()):
            self.modColorList.removeRow(0)
    
    def select_row(self, row):
        self.colorList.selectionModel().clear()
        sel = self.modColorList.createIndex(row,0)
        self.colorList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)
        
    def init_new_palette(self):
        self.clear_palette()
        r = 0
        for i in COLORTABLE:
            item = ColorItem(i)
            self.modColorList.insertRow(r, item)
            r += 1
        self.select_row(r)
        
    def change_color(self):
        """ send the selected color to global """
        sel = self.colorList.selectionModel().selectedIndexes()
        if sel:
            row = sel[0].row()
            global COLOR
            COLOR = row
                    
    def change_canvas_colortable(self, rgba, row):
        """ change the color for all canvas """
        canvas = self.parent.framesWidget.get_all_canvas()
        for i in canvas:
            i.setColor(row, rgba)
        global COLORTABLE
        if row == len(COLORTABLE):
            COLORTABLE.append(rgba)
        else:
            COLORTABLE[row] = rgba
        # update canvas
        canvas = self.parent.framesWidget.get_canvas()
        self.parent.currentFrameChanged.emit(canvas)

        
    def edit_color(self):
        color = QtGui.qRgba(0, 0, 0, 255)
        sel = self.colorList.selectionModel().selectedIndexes()
        if sel:
            row = sel[0].row()
            item = self.modColorList.itemFromIndex(sel[0])
            color = item.get_color()
        
        color, ok = QtGui.QColorDialog.getRgba()
        if not ok:
            return
        item.set_color(color)
        self.change_canvas_colortable(color, row)
        self.change_color()
        
    def add_color_clicked(self):
        """ create a new row with a color item and ask user wath color to put in"""
        color = QtGui.qRgba(0, 0, 0, 255)
        sel = self.colorList.selectionModel().selectedIndexes()
        if sel:
            item = self.modColorList.itemFromIndex(sel[0])
            color = item.get_color()
        
        color, ok = QtGui.QColorDialog.getRgba()
        if not ok:
            return
        
        item = ColorItem(color)
        row = self.modColorList.rowCount()
        self.modColorList.insertRow(row, item)
    
        self.change_canvas_colortable(color, row)
        self.select_row(row)
        

class Canvas(QtGui.QImage):
    """ Canvas for drawing"""
    def __init__(self, w, h=None):
        if not h:
            QtGui.QImage.__init__(self, w)
        else:
            QtGui.QImage.__init__(self, w, h, QtGui.QImage.Format_Indexed8)
            self.setColorTable(COLORTABLE)
            self.fill(0)
            
        self.lastPoint = QtCore.QPoint(0,0)
        
    def load_from_list(self, li):
        x, y = 0, 0
        for i in li:
            self.setPixel(QtCore.QPoint(x, y), i)
            x += 1
            if x >= SIZE[0]:
                x = 0
                y += 1
                
    def clear(self):
        self.fill(0)
            
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
            
    def draw_point(self, point):
        x, y = point.x(), point.y()
        if x >= 0 and x < SIZE[0] and y >= 0 and y < SIZE[1]: 
            self.setPixel(QtCore.QPoint(x, y), COLOR)
        #~ #custom brush
        #~ brush = ((0, 0), (-1, 0), (0, -1), (1, 0), (0, 1))
        #~ for i in brush:
            #~ x, y = point.x() + i[0], point.y() + i[1]
            #~ if x >= 0 and x < SIZE[0] and y >= 0 and y < SIZE[1]: 
                #~ self.setPixel(QtCore.QPoint(x, y), color)
            
    def clic(self, mouseX, mouseY):
        self.draw('point', QtCore.QPoint(mouseX, mouseY))
        self.lastPoint = QtCore.QPoint(mouseX, mouseY)

    def move(self, mouseX, mouseY):
        self.draw('line', QtCore.QPoint(mouseX, mouseY))
        self.lastPoint = QtCore.QPoint(mouseX, mouseY)
        
        
class Bg(QtGui.QPixmap):
    """ background of the scene"""
    def __init__(self):
        QtGui.QPixmap.__init__(self, SIZE[0], SIZE[1])
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
        
        self.change_size()
        self.parent.currentFrameChanged.connect(self.change_frame)
        
    def change_frame(self, canvas):
        self.canvas = canvas
        self.canvasP.convertFromImage(self.canvas)
        self.canvasItem.setPixmap(self.canvasP)
        
    def change_size(self):
        self.scene.setSceneRect(0, 0, SIZE[0], SIZE[1])
        # the background
        self.bg = Bg()
        self.scene.addPixmap(self.bg)
        # a pixmap to display on scene
        self.canvasP = QtGui.QPixmap(SIZE[0], SIZE[1])
        self.canvasP.fill(QtGui.QColor(0, 0, 0, 0))
        self.canvasItem = self.scene.addPixmap(self.canvasP)
        
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
            self.canvas.clic(pos.x(), pos.y())
            self.canvasP.convertFromImage(self.canvas)
            self.canvasItem.setPixmap(self.canvasP)
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
            self.canvas.move(pos.x(), pos.y())
            self.canvasP.convertFromImage(self.canvas)
            self.canvasItem.setPixmap(self.canvasP)
        else:
            return QtGui.QGraphicsView.mouseMoveEvent(self, event)

        
class MainWidget(QtGui.QWidget):
    currentFrameChanged = QtCore.pyqtSignal(object)
    def __init__(self):
        QtGui.QWidget.__init__(self)
        
        ### palette ###
        self.palette = Palette(self)

        ### zoom buttons ###
        self.zoomInW = QtGui.QToolButton()
        self.zoomInW.setAutoRaise(True)
        self.zoomInW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/zoom_in.svg")))
        self.zoomOutW = QtGui.QToolButton()
        self.zoomOutW.setAutoRaise(True)
        self.zoomOutW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/zoom_out.svg")))

        ### labels info ###
        self.imL = QtGui.QLabel("This is an alpha program, full of bug")
        
        ### viewer and framesWidget ###
        self.framesWidget = FramesWidget(self)
        self.scene = Scene(self)
        
        ### connexion ##################################################
        self.zoomInW.clicked.connect(self.zoom_in)
        self.zoomOutW.clicked.connect(self.zoom_out)

        ### layout #####################################################
        grid = QtGui.QGridLayout()
        grid.setSpacing(2)
        grid.addWidget(self.zoomInW, 0, 0)
        grid.addWidget(self.zoomOutW, 0, 1)
        grid.addWidget(self.palette, 1, 0, 2, 4)

        hLayout = QtGui.QHBoxLayout()
        hLayout.setSpacing(2)
        hLayout.addLayout(grid)
        hLayout.addWidget(self.framesWidget)
        hLayout.addWidget(self.scene)
        
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(2)
        layout.addLayout(hLayout)
        
        self.setLayout(layout)  
        
    def zoom_in(self):
        self.scene.scaleView(2)

    def zoom_out(self):
        self.scene.scaleView(0.5)
        
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
        fileMenu.addAction(importAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(exportAction)
        fileMenu.addAction(exitAction)
        
        ### central widget ###
        self.centralWidget = MainWidget()
        self.setCentralWidget(self.centralWidget)
        self.init_canvas()
        
        self.show()
    
        
    def init_canvas(self):
        self.centralWidget.scene.change_size()
        global COLORTABLE
        COLORTABLE = [QtGui.qRgba(0, 0, 0, 0), QtGui.qRgba(0, 0, 0, 255)]
        self.centralWidget.palette.init_new_palette()
        # create the first frame
        self.centralWidget.framesWidget.add_frame_clicked()
        # and select it
        sel = self.centralWidget.framesWidget.modFramesList.createIndex(0,0)
        self.centralWidget.framesWidget.framesList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)
        
    def new_action(self):
        ok, w, h = NewDialog().get_return()
        if ok:
            global SIZE
            SIZE = (w, h)
        self.centralWidget.framesWidget.clear_frames()
        self.centralWidget.palette.clear_palette()
        self.centralWidget.init_canvas()
        
    def open_action(self):
        url = QtGui.QFileDialog.getOpenFileName(self, "open pix file", "", "Pix files (*.pix );;All files (*)")
        if url:
            save = open(url, "r")
            frame = []
            for line in save.readlines():
                if line[0:5] == "COLOR":
                    color = [int(n) for n in line[6:-2].split(',')]
                elif line[0:5] == "SIZE ":
                    size = [int(n) for n in line[6:-2].split(',')]
                elif line[0:5] == "PIXEL":
                    frame.append([int(n) for n in line[6:-2].split(',')])
                elif line[0:5] == "STILL":
                    frame.append(None)
            save.close()
            global SIZE
            SIZE = (size[0], size[1])
            global COLORTABLE
            COLORTABLE = color
            self.centralWidget.framesWidget.init_new_anim(frame)
            self.centralWidget.palette.init_new_palette()
        
    def save_action(self):
        url = QtGui.QFileDialog.getSaveFileName(self, "save pix file", "", "Pix files (*.pix )")
        if url:
            #~ url = os.path.splitext(str(url))[0] + ".pix"
            save = open(url, "w")
            lim = self.centralWidget.framesWidget.get_all_canvas(True)
            col = [int(i) for i in lim[0].colorTable()]
            save.write("COLOR%s\n" %(col))
            save.write("SIZE (%s, %s)\n" %(lim[0].width(), lim[0].height()))
            for im in lim:
                if im:
                    l = []
                    for y in xrange(im.height()):
                        for x in xrange(im.width()):
                            l.append(im.pixelIndex(x, y))
                    s = ','.join(str(n) for n in l)
                    save.write("PIXEL(%s)\n" %(s))
                else:
                    save.write("STILL\n")
            save.close()
    def export_action(self):
        url = QtGui.QFileDialog.getSaveFileName(self, "Export animation as png", "", "Png files (*.png )")
        if url:
            url = os.path.splitext(str(url))[0]
            files = []
            n = 1
            fnexist = False
            for im in self.centralWidget.framesWidget.get_all_canvas(True):
                fn = "%s%s.png" %(url, n)
                if os.path.isfile(fn):
                    fnexist = True
                if im:
                    files.append((fn, im))
                    sim = im
                else:
                    sim.save(fn)
                    files.append((fn, sim))
                n += 1
            if fnexist:
                message = QtGui.QMessageBox()
                message.setWindowTitle("Overwrite?")
                message.setText("Some filename allready exist.\nDo you want to overwrite them?");
                message.setIcon(QtGui.QMessageBox.Warning)
                message.addButton("Cancel", QtGui.QMessageBox.RejectRole)
                message.addButton("Overwrite", QtGui.QMessageBox.AcceptRole)
                ret = message.exec_();
                if ret:
                    for i in files:
                        i[1].save(i[0])
            
        
    def exit_action(self):
        QtGui.qApp.quit()


class NewDialog(QtGui.QDialog):
    def __init__(self, w=64, h=64):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("new animation")
        
        ### instructions ###
        self.instL = QtGui.QLabel("Enter the size of the new animation :")
        ### width ###
        self.wL = QtGui.QLabel("width")
        self.wW = QtGui.QLineEdit(str(w), self)
        self.wW.setValidator(QtGui.QIntValidator(self.wW))
        ### height ###
        self.hL = QtGui.QLabel("height")
        self.hW = QtGui.QLineEdit(str(h), self)
        self.hW.setValidator(QtGui.QIntValidator(self.hW))
        ### error ###
        self.errorL = QtGui.QLabel("")
        ### apply, undo ###
        self.cancelW = QtGui.QPushButton('cancel', self)
        self.cancelW.clicked.connect(self.cancel_clicked)
        self.newW = QtGui.QPushButton('new', self)
        self.newW.clicked.connect(self.new_clicked)

        grid = QtGui.QGridLayout()
        grid.setSpacing(4)
        grid.addWidget(self.instL, 0, 0, 1, 2)
        grid.addWidget(self.wL, 1, 0)
        grid.addWidget(self.hL, 2, 0)
        grid.addWidget(self.wW, 1, 1)
        grid.addWidget(self.hW, 2, 1)
        grid.addWidget(self.errorL, 3, 0, 1, 2)

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

    def new_clicked(self):
        try:
            w = int(self.wW.text())
            h = int(self.hW.text())
        except ValueError:
            self.errorL.setText("ERROR : You must enter a number !")
            return
        if w > 0 and h > 0:
            self.w = w
            self.h = h
            self.accept()
        else:
            self.errorL.setText("ERROR : The size must be greater than 0 !")

    def cancel_clicked(self):
        self.reject()

    def get_return(self):
        if self.result():
            return True , self.w, self.h
        else:
            return False, None, None


if __name__ == '__main__':    
    app = QtGui.QApplication(sys.argv)
    mainWin = MainWindow()
    sys.exit(app.exec_())
    
