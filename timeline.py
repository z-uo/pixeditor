#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from __future__ import division
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt

# change widgetsize on frame/layer change
# copy/paste > frame lenght as object
# organize layers

class Viewer(QtGui.QScrollArea):
    """ QScrollArea you can move with midbutton"""
    resyzing = QtCore.pyqtSignal(tuple)
    def __init__ (self):
        QtGui.QScrollArea.__init__(self)
        self.setAlignment(QtCore.Qt.AlignLeft)
        
    def event(self, event):
        """ capture middle mouse event to move the view """
        # clic: save position
        if   (event.type() == QtCore.QEvent.MouseButtonPress and
              event.button() == QtCore.Qt.MidButton):
            self.mouseX,  self.mouseY = event.x(), event.y()
            return True
        # drag: move the scrollbars
        elif (event.type() == QtCore.QEvent.MouseMove and
               event.buttons() == QtCore.Qt.MidButton):
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - (event.x() - self.mouseX))
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - (event.y() - self.mouseY))
            self.mouseX,  self.mouseY = event.x(), event.y()
            return True
        elif (event.type() == QtCore.QEvent.Resize):
            self.resyzing.emit((event.size().width(), event.size().height()))
        return QtGui.QScrollArea.event(self, event)

class LayersCanvas(QtGui.QWidget):
    """ Widget containing the canvas list """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setFixedWidth(60)
        
        self.white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        self.black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        self.font = QtGui.QFont('SansSerif', 8, QtGui.QFont.Normal)
        self.layerH = 20
        self.margeH = 22
        
    def paintEvent(self, ev=''):
        lH, mH = self.layerH, self.margeH
        p = QtGui.QPainter(self)
        p.setPen(QtGui.QPen(self.black))
        p.setFont(self.font)
        
        # background
        p.fillRect (0, 0, self.width(), mH-2, self.white)
        p.drawLine (0, mH-2, self.width(), mH-2)
        # currentLayer
        p.fillRect(0, (self.parent.project.currentLayer * lH) + mH-1,
                   self.width(), lH, self.white)
        # layer's names
        y = mH
        for i, layer in enumerate(self.parent.project.frames, 1):
            y += lH
            #~ y = (i * lH) + mH
            p.drawText(4, y-6, layer["name"])
            p.drawLine (0, y-1, self.width(), y-1)
        
    def event(self, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress and
                       event.button()==QtCore.Qt.LeftButton):
            item = self.layer_at(event.y())
            if item is not None:
                self.parent.project.currentLayer = item
                self.update()
        return QtGui.QWidget.event(self, event)
    
    def layer_at(self, y):
        l = (y - 23) // 20
        if 0 <= l < len(self.parent.project.frames):
            return l
        return None
            
        
class TimelineCanvas(QtGui.QWidget):
    """ widget containing the timeline """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        self.grey = QtGui.QBrush(QtGui.QColor(193, 193, 193))
        self.white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        self.whitea = QtGui.QBrush(QtGui.QColor(255, 255, 255, 127))
        self.black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        self.frameWidth = 13
        self.frameHeight = 20
        self.margeX = 1
        self.margeY = 22
        self.strechFrame = False
        self.setMinimumSize(self.getMiniSize()[0], self.getMiniSize()[1])

    def paintEvent(self, ev=''):
        fW, fH = self.frameWidth, self.frameHeight
        mX, mY = self.margeX, self.margeY
        p = QtGui.QPainter(self)
        fontLight = QtGui.QFont('SansSerif', 7, QtGui.QFont.Light)
        fontBold = QtGui.QFont('SansSerif', 8, QtGui.QFont.Normal)
        p.setPen(QtGui.QPen(self.grey))
        p.setBrush(self.whitea)
        
        # background
        p.fillRect (0, 0, self.width(), 21, self.white)
        p.drawLine (0, 21, self.width(), 21)
        for j, i in enumerate(xrange(7, self.width(), fW), 1):
            p.drawLine (i-7, 19, i-7, 21)
            
            if j % 5 == 0:
                p.setFont(fontLight)
                metrics = p.fontMetrics()
                fw = metrics.width(str(j))
                p.drawText(i-fw/2, 17, str(j))
            
            if j % self.parent.project.fps == 0:
                p.setFont(fontBold)
                metrics = p.fontMetrics()
                s = str(j//self.parent.project.fps)
                fw = metrics.width(s)
                p.drawText(i-fw/2, 10, s)
        
        if self.parent.selection:
            l = self.parent.selection[0]
            f1, f2 = self.parent.selection[1], self.parent.selection[2]
            # remet a l'endroit
            if f2 < f1:
                f1, f2, = f2, f1
            p.fillRect((f1 * fW) + mX, (l * fH) + mY, 
                       (f2 - f1 + 1) * fW, fH, self.white)
            
        # current frame
        p.drawLine(self.parent.project.currentFrame*fW, 0, 
                   self.parent.project.currentFrame*fW, self.height())
        p.drawLine(self.parent.project.currentFrame*fW + fW , 0, 
                   self.parent.project.currentFrame*fW + fW , self.height())
        framesRects = []
        strechRects = []
        self.strechBoxList = []
        for y, layer in enumerate(self.parent.project.frames):
            self.strechBoxList.append([])
            for x, frame in enumerate(layer["frames"]):
                if frame:
                    w, h = 9, 17
                    s = x
                    while s+1 < len(layer["frames"]) and not layer["frames"][s+1]:
                        s += 1
                        w += 13
                    nx = x * fW + mX + 1
                    ny = y * fH + mY + 1
                    framesRects.append(QtCore.QRect(nx, ny, w, h))
                    strechrect = QtCore.QRect(nx+w-9, ny+h-9, 9, 9)
                    strechRects.append(strechrect)
                    self.strechBoxList[y].append(strechrect)
                else:
                    self.strechBoxList[y].append(False)
        p.drawRects(framesRects)
        p.setBrush(self.white)
        p.drawRects(strechRects)
        
    def getMiniSize(self):
        """ return the minimum size of the widget 
            to display all frames and layers """
        minH = (len(self.parent.project.frames)*self.frameHeight) + self.margeY
        #get the longest layer
        maxF = max([len(l["frames"]) for l in self.parent.project.frames])
        minW = (maxF * self.frameWidth) + self.margeX
        return (minW, minH)
        
    def event(self, event):
        if   (event.type() == QtCore.QEvent.MouseButtonPress and
              event.button()==QtCore.Qt.LeftButton):
            frame = self.frame_at(event.x())
            layer = self.layer_at(event.y())
            if frame is not None and layer is not None:
                strech = self.is_in_strech_box(event.pos())
                if strech is not None:
                    self.strechFrame = (strech[1], frame)
                    self.parent.selection = False
                else:
                    self.parent.selection = [layer, frame, frame]
                    self.strechFrame = False
            else:
                self.strechFrame = False
                self.parent.selection = False
            self.parent.layersCanvas.update()
            self.update()
            self.parent.change_current(frame, layer)
            return True
        elif (event.type() == QtCore.QEvent.MouseMove and
              event.buttons() == QtCore.Qt.LeftButton):
            frame = self.frame_at(event.x())
            layer = self.layer_at(event.y())
            if frame is not None:
                if self.parent.selection:
                    self.parent.selection[2] = frame
            if     (layer is not None and not self.strechFrame and
                    not self.parent.selection):
                self.parent.project.currentLayer = layer
            self.strech(frame)
            self.parent.layersCanvas.update()
            self.update()
            self.parent.change_current(frame, layer)
            return True
        return QtGui.QWidget.event(self, event)
        
    def is_in_strech_box(self, pos):
        for layer, i in enumerate(self.strechBoxList):
            for frame, j in enumerate(i):
                if j and j.contains(pos):
                    return (frame, layer)
        return None
        
    def strech(self, f):
        if self.strechFrame:
            sl, sf = self.strechFrame[0], self.strechFrame[1]
            while f > sf:
                self.parent.project.frames[sl]["frames"].insert(sf+1, 0)
                sf += 1
            while f < sf:
                if not self.parent.project.frames[sl]["frames"][sf]:
                    self.parent.project.frames[sl]["frames"].pop(sf)
                    sf -= 1
                else:
                    break
            self.parent.adjust_size()
            self.strechFrame = (sl, sf)
        
    def frame_at(self, x):
        s = (x - self.margeX)  // self.frameWidth
        if 0 <= s <= self.width() // self.frameWidth:
            return s
        return None
        
    def layer_at(self, y):
        l = ((y - self.margeY) // self.frameHeight)
        if 0 <= l < len(self.parent.project.frames):
            return l
        return None
        
        
########################################################################
class Timeline(QtGui.QWidget):
    """ widget containing timeline, layers and all their buttons """
    def __init__(self, project):
        QtGui.QWidget.__init__(self)
        self.project = project
        
        self.selection = False
        self.toPaste = False
        
        ### viewer ###
        self.layersCanvas = LayersCanvas(self)
        self.layersV = Viewer()
        self.layersV.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layersV.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.layersV.setWidget(self.layersCanvas)
        
        self.timelineCanvas = TimelineCanvas(self)
        self.timelineV = Viewer()
        self.timelineV.setWidget(self.timelineCanvas)
        self.timelineV.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.timelineV.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.timeVSize = (0, 0)
        self.timelineV.resyzing.connect(self.adjust_size)
        
        self.layersV.verticalScrollBar().valueChanged.connect(
                lambda v: self.timelineV.verticalScrollBar().setValue(v))
        self.timelineV.verticalScrollBar().valueChanged.connect(
                lambda v: self.layersV.verticalScrollBar().setValue(v))
        self.project.update_timeline.connect(self.timelineCanvas.update)
        self.project.update_timeline.connect(self.layersCanvas.update)
        
        ### shortcuts ###
        shortcut = QtGui.QShortcut(self)
        shortcut.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_X))
        shortcut.activated.connect(self.cut)
        shortcopy = QtGui.QShortcut(self)
        shortcopy.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_C))
        shortcopy.activated.connect(self.copy)
        shortpaste = QtGui.QShortcut(self)
        shortpaste.setKey(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_V))
        shortpaste.activated.connect(self.paste)
        
        ### adding and deleting images ###
        self.addFrameW = QtGui.QToolButton()
        self.addFrameW.setAutoRaise(True)
        self.addFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_add.png")))
        self.addFrameW.clicked.connect(self.add_frame_clicked)
        self.dupFrameW = QtGui.QToolButton()
        self.dupFrameW.setAutoRaise(True)
        self.dupFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_dup.png")))
        self.dupFrameW.clicked.connect(self.duplicate_frame_clicked)
        self.delFrameW = QtGui.QToolButton()
        self.delFrameW.setAutoRaise(True)
        self.delFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_del.png")))
        self.delFrameW.clicked.connect(self.delete_frame_clicked)
        self.clearFrameW = QtGui.QToolButton()
        self.clearFrameW.setAutoRaise(True)
        self.clearFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/frame_clear.png")))
        self.clearFrameW.clicked.connect(self.clear_frame_clicked)

        ### adding and deleting layers ###
        self.addLayerW = QtGui.QToolButton()
        self.addLayerW.setAutoRaise(True)
        self.addLayerW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/layer_add.png")))
        self.addLayerW.clicked.connect(self.add_layer_clicked)
        self.dupLayerW = QtGui.QToolButton()
        self.dupLayerW.setAutoRaise(True)
        self.dupLayerW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/layer_dup.png")))
        self.dupLayerW.clicked.connect(self.duplicate_layer_clicked)
        self.delLayerW = QtGui.QToolButton()
        self.delLayerW.setAutoRaise(True)
        self.delLayerW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/layer_del.png")))
        self.delLayerW.clicked.connect(self.delete_layer_clicked)
        
        ### play the animation ###
        self.playFrameW = QtGui.QToolButton()
        self.playFrameW.state = "play"
        self.playFrameW.setAutoRaise(True)
        self.playFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_play.png")))
        self.playFrameW.clicked.connect(self.play_pause_clicked)
        self.fpsL = QtGui.QLabel("fps")
        self.fpsW = QtGui.QLineEdit(self)
        self.fpsW.setText(str(12))
        valid = QtGui.QIntValidator()
        valid.setRange(1, 60)
        self.fpsW.setValidator(valid)
        self.fpsW.textChanged.connect(self.fps_changed)

        self.repeatW = QtGui.QToolButton()
        self.repeatW.state = False
        self.repeatW.setAutoRaise(True)
        self.repeatW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_no_repeat.png")))
        self.repeatW.clicked.connect(self.repeat_clicked)

        ### layout ###
        layout = QtGui.QGridLayout()
        layout.setSpacing(4)
        layout.addWidget(self.addLayerW, 0, 0)
        layout.addWidget(self.dupLayerW, 1, 0)
        layout.addWidget(self.delLayerW, 2, 0)
        layout.addWidget(self.layersV, 0, 1, 4, 1)
        layout.addWidget(self.timelineV, 0, 2, 4, 9)
        layout.addWidget(self.addFrameW, 4, 2)
        layout.addWidget(self.dupFrameW, 4, 3)
        layout.addWidget(self.delFrameW, 4, 4)
        layout.addWidget(self.clearFrameW, 4, 5)
        layout.setColumnStretch(6, 2)
        layout.addWidget(self.fpsW, 4, 7)
        layout.addWidget(self.fpsL, 4, 8)
        layout.addWidget(self.repeatW, 4, 9)
        layout.addWidget(self.playFrameW, 4, 10)
        self.setLayout(layout)

    def change_current(self, frame=None, layer=None):
        if not self.project.playing:
            if frame is not None:
                self.project.currentFrame = frame
            if layer is not None:
                self.project.currentLayer = layer
            if frame is not None or layer is not None:
                self.project.update_view.emit()
            
    ######## Size adjust ###############################################
    def showEvent(self, event):
        self.timelineCanvas.setMinimumHeight(len(self.project.frames)*20 + 25)
        self.timelineCanvas.update()
        self.layersCanvas.setMinimumHeight(self.timelineCanvas.height())
        self.layersCanvas.update()
        self.layersV.setViewportMargins(0, 0, 0, 
                    self.timelineV.horizontalScrollBar().height())
        self.layersV.setMinimumWidth(self.layersCanvas.width() + 
                    self.layersV.verticalScrollBar().width() + 2)
        self.layersV.setMaximumWidth(self.layersCanvas.width() + 
                    self.layersV.verticalScrollBar().width() + 2)
        
    def adjust_size(self, timeVSize=False):
        if timeVSize:
            self.timeVSize = timeVSize
        else:
            timeVSize = self.timeVSize
        wW = timeVSize[0]
        wH = timeVSize[1] - self.timelineV.horizontalScrollBar().height()
        timeMin = self.timelineCanvas.getMiniSize()
        self.timelineCanvas.setFixedWidth(timeMin[0] + wW - self.timelineCanvas.frameWidth)
        if timeMin[1] > wH-2:
            self.timelineCanvas.setFixedHeight(timeMin[1])
            self.layersCanvas.setFixedHeight(timeMin[1])
        else:
            self.timelineCanvas.setFixedHeight(wH-2)
            self.layersCanvas.setFixedHeight(wH-2)
        self.timelineCanvas.update()
        self.layersCanvas.update()
    
    ######## Copy ######################################################
    def cut(self):
        print "cut"
        if self.selection:
            l = self.selection[0]
            f1, f2 = self.selection[1], self.selection[2]
            if f2 < f1:
                f1, f2, = f2, f1
            # copy frames
            self.toPaste = self.project.frames[l]["frames"][f1:f2+1]
            # check if first frame is a real canvas
            trueFrame = self.project.get_true_frame((f1, l), True)
            if trueFrame != (f1, l):
                self.toPaste[0] = self.project.make_canvas(self.project.frames[l]["frames"][trueFrame[0]])
            # check if frame next to selection is a real canvas
            trueFrame2 = self.project.get_true_frame((f2+1, l), True)
            if trueFrame2 and trueFrame != trueFrame2:
                self.project.frames[l]["frames"][f2+1] = self.project.make_canvas(self.project.frames[l]["frames"][trueFrame2[0]])
            # delete cutted frames
            del self.project.frames[l]["frames"][f1:f2+1]
            self.timelineCanvas.update()
            
    def copy(self):
        print "copy"
        if self.selection:
            l = self.selection[0]
            f1, f2 = self.selection[1], self.selection[2]
            if f2 < f1:
                f1, f2, = f2, f1
            # copy frames
            self.toPaste = self.project.frames[l]["frames"][f1:f2+1]
            # check if first frame is a real canvas
            trueFrame = self.project.get_true_frame((f1, l), True)
            if trueFrame != (f1, l):
                self.toPaste[0] = self.project.frames[l]["frames"][trueFrame[0]]
            # make a real copy of all canvas
            for n, canvas in enumerate(self.toPaste):
                if canvas:
                    self.toPaste[n] = self.project.make_canvas(canvas)
        
    def paste(self):
        print "paste"
        if self.toPaste:
            f = self.project.currentFrame
            l = self.project.currentLayer
            while f > len(self.project.frames[l]["frames"]):
                self.project.frames[l]["frames"].append(0)
            for n, canvas in enumerate(self.toPaste):
                self.project.frames[l]["frames"].insert(f+n, canvas)
            self.timelineCanvas.update()
            self.project.update_view.emit()
            
    ######## Buttons ###################################################
    def add_frame_clicked(self):
        layer = self.project.frames[self.project.currentLayer]["frames"]
        frame = self.project.currentFrame
        while frame >= len(layer):
            layer.append(0)
        if layer[frame]:
            layer.insert(frame, self.project.make_canvas())
        else:
            layer[frame] = self.project.make_canvas()
        self.adjust_size()
        self.project.update_view.emit()
        
    def duplicate_frame_clicked(self):
        layer = self.project.frames[self.project.currentLayer]["frames"]
        frame = self.project.currentFrame
        while frame >= len(layer):
            layer.append(0)
        f = self.project.make_canvas(self.project.get_true_frame())
        if layer[frame]:
            layer.insert(frame, f)
        else:
            layer[frame] = f
        self.adjust_size()
        self.project.update_view.emit()
        
    def delete_frame_clicked(self):
        layer = self.project.frames[self.project.currentLayer]["frames"]
        frame = self.project.currentFrame
        if frame >= len(layer):
            return
        if len(layer) == 1 and frame == 0:
            layer[frame].clear()
        elif (layer[frame] and 
              not frame + 1 >= len(layer) and 
              not layer[frame + 1]):
            layer.pop(frame + 1)
        else:
            layer.pop(frame)
        self.adjust_size()
        self.project.update_view.emit()
        
    def clear_frame_clicked(self):
        f = self.project.get_true_frame()
        if f:
            f.clear()
            self.project.update_view.emit()
        
    def add_layer_clicked(self):
        self.project.frames.insert(self.project.currentLayer + 1, 
                                   self.project.make_layer())
        self.project.currentLayer += 1
        self.adjust_size()
        self.project.update_view.emit()
        
    def duplicate_layer_clicked(self):
        self.project.frames.insert(self.project.currentLayer + 1,
                self.project.make_layer(
                self.project.frames[self.project.currentLayer]))
        self.project.currentLayer += 1
        self.adjust_size()
        self.project.update_view.emit()
        
    def delete_layer_clicked(self):
        del self.project.frames[self.project.currentLayer]
        self.project.currentLayer = 0
        if not self.project.frames:
            self.project.frames.append(self.project.make_layer())
        self.adjust_size()
        self.project.update_view.emit()

    ######## Play ######################################################
    def fps_changed(self):
        try:
            f = int(self.fpsW.text())
        except ValueError:
            self.fpsW.setText("1")
            return
        if f == 0:
            self.fpsW.setText("1")
            return
        self.project.fps = f
        self.timelineCanvas.update()

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
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.animate)
            self.f = self.project.currentFrame
            self.fps = self.project.fps
            self.project.playing = True
            maxF = max([len(l["frames"]) for l in self.project.frames])
            if self.project.currentFrame+1 >= maxF:
                self.project.currentFrame = 0
                self.timelineCanvas.update()
                self.project.update_view.emit()
            self.timer.start(1000//self.fps)
        elif self.playFrameW.state == 'stop':
            self.play_end()
            
    def play_end(self):
        self.timer.stop()
        self.playFrameW.state = "play"
        self.playFrameW.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_play.png")))
        self.project.playing = False
        
    def animate(self):
        if self.fps != self.project.fps:
            self.fps = self.project.fps
            self.timer.setInterval(1000//self.fps)
        maxF = max([len(l["frames"]) for l in self.project.frames])
        self.f = self.project.currentFrame + 1
        if self.f < maxF:
            self.project.currentFrame = self.f
            self.timelineCanvas.update()
            self.project.update_view.emit()
        else:
            if self.repeatW.state:
                self.project.currentFrame = 0
                self.timelineCanvas.update()
                self.project.update_view.emit()
            else:
                self.play_end()
            
