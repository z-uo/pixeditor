#!/usr/bin/env python3

from __future__ import division
import sys
import time
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt

# DONE add play function 
# DONE add custom framerate, stop button, repeat
# add play from here, foreward/backward repeat, play backward > advanced control
# DONE add still image in timeline > gerer supression
# DONE always one frame selected
# DONE bug when deleting the last frame
# add icones with update on mouserelese
# DONE duplicate frame (make a still frame drawable)
# DONE clear frame (create new on a still frame)
# add new canvas / resize / import / export
# add onionskin
# ALMOST DONE add palette
# DONE add palette: change color on doubleclic
# add indexed color
# add copy paste move frame
# add move frame content
# add custom brushes
# add layers


### global ###
# drawing color
COLOR = QtGui.QColor(0, 0, 0, 255)
# drawing brush
PEN = 1
# mode draw/erase
MODE = 'draw'
# canvas size
SIZE = (64, 64)


class Item(QtGui.QStandardItem):
    """ a QStandartItem that contain a Canvas """
    def __init__(self, image=None):
        QtGui.QStandardItem.__init__(self)
        self.image = image
        if self.image:
            self.isStill = False
        else:
            self.isStill = True
            
    def set_image(self, image=None):
        self.image = image
        if self.image:
            self.isStill = False
        else:
            self.isStill = True
    def get_image(self):
        return self.image
        
        
class FramesWidget(QtGui.QWidget):
    """ manages the frames """
    frameChanged = QtCore.pyqtSignal(object)
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        
        ### model to store images ###
        self.modFramesList = QtGui.QStandardItemModel(0, 1)

        ### listview to display images ###
        self.framesList = QtGui.QTableView()
        self.framesList.setModel(self.modFramesList)
        self.framesList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.framesList.selectionModel().selectionChanged.connect(self.change_frame)
        
        # try to make an icon
        self.framesList.setIconSize(QtCore.QSize(32, 32))
        # try to move frame by drag drop
        self.framesList.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.framesList.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        
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
    
    def select_frame(self, frame):
        """ select a frame which call self.change_frame() """
        self.framesList.selectionModel().clear()
        sel = self.modFramesList.createIndex(frame,0)
        self.framesList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)
        
    def insert_item(self, item):
        # insert it after the selection or in the end
        sel = self.framesList.selectionModel().selectedIndexes()
        if sel:
            row = sel[0].row()+1
        else:
            row = self.modFramesList.rowCount()
        self.modFramesList.insertRow(row, item)
        self.select_frame(row)
        
    def change_frame(self):
        """ send the selected canvas to the viewer """
        sel = self.framesList.selectionModel().selectedIndexes()
        if sel:
            item = self.modFramesList.itemFromIndex(sel[0])
            if item:
                img = item.get_image()
                if img:
                    self.frameChanged.emit(img)
                else:
                    sel = sel[0]
                    i = 1
                    while not img and sel.row()-i >= 0:
                        item = self.modFramesList.item(sel.row()-i,0)
                        img = item.get_image()
                        i = i + 1
                    self.frameChanged.emit(img)
                    
    def add_frame_clicked(self, qimg=None):
        """ create a new row and a canvas inside """
        # create the canvas and the item haning it on FramesWidget
        if qimg:
            img = Canvas(qimg.copy(0, 0, SIZE[0], SIZE[1]))
        else:
            img = Canvas(SIZE[0], SIZE[1])
            
        item = Item(img)
        item.setText('frame')
        self.insert_item(item)
        
    def still_frame_clicked(self):
        """ add a still frame after the current """
        item = Item()
        item.setText('  -')
        self.insert_item(item)
    
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
                img = Canvas(SIZE[0], SIZE[1], QtGui.QImage.Format_ARGB32)
                item.set_image(img)
                item.setText('frame')
                self.select_frame(0)
        # else, jst select the previous frame
        else:
            self.select_frame(row - 1)
        
    def duplicate_frame_clicked(self):
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
        sel = self.framesList.selectionModel().selectedIndexes()
        if sel:
            item = self.modFramesList.itemFromIndex(sel[0])
            img = item.get_image()
            if img:
                img.clear()
            else:
                img = Canvas(SIZE[0], SIZE[1], QtGui.QImage.Format_ARGB32)
                item.set_image(img)
                item.setText('frame')
        self.change_frame()
        
    def framerate_changed(self):
        f = int(self.framerateW.text())
        if f:
            self.framerate = 1/f
            print self.framerate
        
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
        for i in range(self.rows):
            if not self.stop:
                self.frame.emit(i)
                time.sleep(self.parent.framerate)
        

class ColorItem(QtGui.QStandardItem):
    """ a QStandartItem that contain a Color """
    def __init__(self, color=QtGui.QColor(0, 0, 0, 255)):
        QtGui.QStandardItem.__init__(self)
        self.color = color
    def set_color(self, color=QtGui.QColor(0, 0, 0, 255)):
        self.color = color
    def get_color(self):
        return self.color
        
        
class Palette(QtGui.QWidget):
    """ color palette """
    colorChanged = QtCore.pyqtSignal(object)
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
        
        self.colorList.setIconSize(QtCore.QSize(32, 32))
        # try to move frame by drag drop
        self.colorList.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.colorList.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        
        ### adding and deleting color ###
        self.addColorW = QtGui.QPushButton('add')
        self.addColorW.clicked.connect(self.add_color_clicked)
        self.delColorW = QtGui.QPushButton('delete')
        self.delColorW.clicked.connect(self.delete_color_clicked)

        ### layout ###
        toolBox = QtGui.QHBoxLayout()
        toolBox.addWidget(self.addColorW)
        toolBox.addWidget(self.delColorW)
        toolBox.addStretch(0)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.colorList)
        self.layout.addLayout(toolBox)
        
    def change_color(self):
        """ send the selected color to global """
        sel = self.colorList.selectionModel().selectedIndexes()
        if sel:
            item = self.modColorList.itemFromIndex(sel[0])
            if item:
                color = item.get_color()
                if color:
                    global COLOR
                    COLOR = color
                    
    def select_color(self, row):
        self.colorList.selectionModel().clear()
        sel = self.modColorList.createIndex(row,0)
        self.colorList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)
        
    def edit_color(self):
        color = QtGui.QColor(0, 0, 0, 255)
        sel = self.colorList.selectionModel().selectedIndexes()
        if sel:
            item = self.modColorList.itemFromIndex(sel[0])
            color = item.get_color()
                
        color = QtGui.QColorDialog.getColor(COLOR)
        if not color.isValid():
            return
        
        item.set_color(color)
        colorIcon = QtGui.QPixmap(32, 32)
        colorIcon.fill(color)
        item.setIcon(QtGui.QIcon(colorIcon))
        
        self.change_color()
        
    def add_color_clicked(self):
        """ create a new row with a color item and ask user wath color to put in"""
        color = QtGui.QColor(0, 0, 0, 255)
        sel = self.colorList.selectionModel().selectedIndexes()
        if sel:
            item = self.modColorList.itemFromIndex(sel[0])
            color = item.get_color()
                
        color = QtGui.QColorDialog.getColor(COLOR)
        if not color.isValid():
            return
        
        item = ColorItem(color)
        # insert it after the selection or in the end
        sel = self.colorList.selectionModel().selectedIndexes()
        if sel:
            row = sel[0].row()+1
        else:
            row = self.modColorList.rowCount()
        self.modColorList.insertRow(row, item)
    
        colorIcon = QtGui.QPixmap(32, 32)
        colorIcon.fill(color)
        item.setIcon(QtGui.QIcon(colorIcon))
        
        self.select_color(row)
        
    def delete_color_clicked(self):
        """ delete selected frame from the model"""
        sel = self.colorList.selectionModel().selectedIndexes()
        row = sel[0].row()
        self.modColorList.removeRow(row)
        if self.modColorList.rowCount() == 0:
            self.add_color_clicked()
        elif row == 0 :
            self.select_color(0)
        else:
            self.select_color(row - 1)
        

class Canvas(QtGui.QImage):
    """ Canvas for drawing"""
    def __init__(self, w, h=None):
        if h is None:
            QtGui.QImage.__init__(self, w)
        else:
            QtGui.QImage.__init__(self, w, h, QtGui.QImage.Format_Indexed8)
            self.setColor(0, QtGui.qRgba(0, 0, 0, 0))
            self.setColor(1, QtGui.qRgb(0, 0, 0))
        
            self.fill(0)
        self.lastPoint = QtCore.QPoint(0,0)
        
    def clear(self):
        self.fill(0)
            
    def draw(self, fig, p2):
        if MODE == 'erase':
            color = 0
        else:
            color = 1
        if fig == 'point':
            self.setPixel (p2, color)
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
                    self.setPixel(QtCore.QPoint(x, y), color)
                self.setPixel(p2, color)
            else:
                for i in xrange(abs(p1.y()-p2.y())):
                    if p1.y()-p2.y() < 0:
                        y = p1.y() + i
                    else:
                        y = p1.y() - i
                    x = int( (p2.x()-p1.x()) / (p2.y() - p1.y()) * (y - p1.y()) + p1.x() + 0.5)
                    self.setPixel(QtCore.QPoint(x, y), color)
                self.setPixel(p2, color)
            

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
        self.bg = Bg()
        
        # the canvas to draw on
        self.canvas = False
        # a pixmap to display on scene
        self.canvasP = QtGui.QPixmap(SIZE[0], SIZE[1])
        self.canvasP.fill(QtGui.QColor(0, 0, 0, 0))
        self.zoomN = 1
        
        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.scene.setSceneRect(0, 0, SIZE[0], SIZE[1])
        self.scene.addPixmap(self.bg)
        self.canvasItem = self.scene.addPixmap(self.canvasP)
        self.setScene(self.scene)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.setMinimumSize(400, 400)
        
        self.parent.framesWidget.frameChanged.connect(self.change_frame)
        
    def change_frame(self, canvas):
        self.canvas = canvas
        self.canvasP.convertFromImage(self.canvas)
        self.canvasItem.setPixmap(self.canvasP)
        
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
    
    def __init__(self):
        QtGui.QWidget.__init__(self)

        ### draw ###
        self.drawW = QtGui.QToolButton(self)
        self.drawW.setAutoRaise(True)
        self.drawW.setIcon(QtGui.QIcon(QtGui.QPixmap('icons/draw.svg')))
        
        ### erase ###
        self.eraseW = QtGui.QToolButton(self)
        self.eraseW.setAutoRaise(True)
        self.eraseW.setIcon(QtGui.QIcon(QtGui.QPixmap('icons/eraser.svg')))
        

        ### color ###
        #~ self.color = QtGui.QColor(0, 0, 0)
        #~ self.colorIcon = QtGui.QPixmap(22, 22)
        #~ self.colorIcon.fill(self.color)
#~ 
        #~ self.colorW = QtGui.QToolButton(self)
        #~ self.colorW.setAutoRaise(True)
        #~ self.colorW.setIcon(QtGui.QIcon(self.colorIcon))
        
        self.palette = Palette(self)
        
        ### pen size ###
        self.penW = QtGui.QComboBox(self)
        self.penW.addItem("1")
        self.penW.addItem("2")
        self.penW.addItem("3")
        self.penW.addItem("4")
        self.penW.addItem("5")
        self.penW.addItem("6")
        self.penW.addItem("7")
        self.penW.addItem("8")
        self.penW.addItem("9")
        self.penW.addItem("10")

        ### zoom buttons ###
        self.zoomInW = QtGui.QToolButton()
        self.zoomInW.setAutoRaise(True)
        self.zoomInW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/zoom_in.svg")))
        self.zoomOutW = QtGui.QToolButton()
        self.zoomOutW.setAutoRaise(True)
        self.zoomOutW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/zoom_out.svg")))

        ### labels info ###
        self.imL = QtGui.QLabel("sans titre.png")
        
        ### viewer and framesWidget ###
        self.framesWidget = FramesWidget(self)
        self.viewer = Scene(self)
        # create the first frame
        self.framesWidget.add_frame_clicked()
        # and select it
        sel = self.framesWidget.modFramesList.createIndex(0,0)
        self.framesWidget.framesList.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)
        
        ### connexion ##################################################
        self.drawW.clicked.connect(self.draw_mode)
        self.eraseW.clicked.connect(self.erase_mode)
        #~ self.colorW.clicked.connect(self.color_clicked)
        self.penW.activated[str].connect(self.pen_clicked)  

        self.zoomInW.clicked.connect(self.zoom_in)
        self.zoomOutW.clicked.connect(self.zoom_out)

        ### layout #####################################################
        
        grid = QtGui.QGridLayout()
        grid.setSpacing(2)
        grid.addWidget(self.drawW, 0, 0)
        grid.addWidget(self.eraseW, 0, 1)
        
        grid.addWidget(self.penW, 0, 2)
        
        grid.addWidget(self.zoomInW, 1, 0)
        grid.addWidget(self.zoomOutW, 1, 1)
        grid.addWidget(self.palette, 2, 0, 2, 4)
        
        #~ toolBox = QtGui.QHBoxLayout()
        #~ toolBox.addWidget(self.drawW)
        #~ toolBox.addWidget(self.eraseW)
        #~ toolBox.addWidget(self.colorW)
        #~ toolBox.addWidget(self.penW)
        #~ toolBox.addWidget(self.zoomInW)
        #~ toolBox.addWidget(self.zoomOutW)
        #~ toolBox.addWidget(self.imL)
        #~ toolBox.addStretch(0)

        hLayout = QtGui.QHBoxLayout()
        hLayout.setSpacing(2)
        hLayout.addLayout(grid)
        hLayout.addWidget(self.framesWidget)
        hLayout.addWidget(self.viewer)
        
        ### layout ###
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(2)
        #~ layout.addLayout(toolBox)
        layout.addLayout(hLayout)
        
        self.setLayout(layout)  

    def zoom_in(self):
        self.viewer.scaleView(2)

    def zoom_out(self):
        self.viewer.scaleView(0.5)
        
    def draw_mode(self):
        global MODE
        MODE = 'draw'
        
    def erase_mode(self):
        global MODE
        MODE = 'erase'
        
    def change_frame(self, pixmap):
        self.viewer.setCanvas(pixmap)
        
    def color_clicked(self):
        global COLOR
        color = QtGui.QColorDialog.getColor(COLOR)
        if color.isValid():
            COLOR = color
            self.colorIcon.fill(color)
            self.colorW.setIcon(QtGui.QIcon(self.colorIcon))
            
    def pen_clicked(self, text):
        global PEN
        PEN = text.toInt()[0]
        
        
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
        # import
        importAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Import', self)
        importAction.setShortcut('Ctrl+I')
        importAction.setStatusTip('import frames')
        importAction.triggered.connect(self.import_action)
        # export
        exportAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Export', self)
        exportAction.setShortcut('Ctrl+E')
        exportAction.setStatusTip('Export frames')
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
        fileMenu.addAction(exportAction)
        fileMenu.addAction(exitAction)
        
        ### central widget ###
        self.centralWidget = MainWidget()
        self.setCentralWidget(self.centralWidget)
        
        self.show()
    
    def new_action(self):
        print("new")
        # change size
        # reset FramesWigget
    def import_action(self):
        print("import")
        
    def export_action(self):
        print("export")
    def exit_action(self):
        print("exit")
        QtGui.qApp.quit()


if __name__ == '__main__':    
    app = QtGui.QApplication(sys.argv)
    mainWin = MainWindow()
    sys.exit(app.exec_())
    
