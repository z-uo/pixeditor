#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# Python 3 Compatibility
from __future__ import division
from __future__ import print_function

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt
from dialogs import RenameLayerDialog
from widget import Button, Viewer


class LayersCanvas(QtGui.QWidget):
    """ Widget containing the canvas list """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setFixedWidth(100)
        
        self.white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        self.black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        self.grey = QtGui.QBrush(QtGui.QColor(0, 0, 0, 30))
        self.font = QtGui.QFont('SansSerif', 8, QtGui.QFont.Normal)
        self.layerH = 20
        self.margeH = 22
        self.visibleList = []
        
    def paintEvent(self, ev=''):
        lH, mH = self.layerH, self.margeH
        p = QtGui.QPainter(self)
        p.setPen(QtGui.QPen(self.black))
        p.setBrush(QtGui.QBrush(self.white))
        p.setFont(self.font)
        self.visibleList = []
        
        # background
        p.fillRect (0, 0, self.width(), self.height(), self.grey)
        p.fillRect (0, 0, self.width(), mH-2, self.white)
        p.drawLine (0, mH-2, self.width(), mH-2)
        p.drawPixmap(82, 2, QtGui.QPixmap("icons/layer_eye.png"))
        # curLayer
        p.fillRect(0, (self.parent.project.curLayer * lH) + mH-1,
                   self.width(), lH, self.white)
        # layer's names
        y = mH
        for i, layer in enumerate(self.parent.project.timeline, 1):
            y += lH
            p.drawText(4, y-6, layer.name)
            p.drawLine (0, y-1, self.width(), y-1)
            rect = QtCore.QRect(82, y-19, 15, 15)
            self.visibleList.append(rect)
            p.drawRect(rect)
            if layer.visible:
                p.fillRect(84, y-17, 12, 12, self.black)
        
    def event(self, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress and
                       event.button()==QtCore.Qt.LeftButton):
            item = self.layerAt(event.y())
            if item is not None:
                self.parent.project.curLayer = item
                if self.visibleList[item].contains(event.pos()):
                    if self.parent.project.timeline[item].visible:
                        self.parent.project.timeline[item].visible = False
                    else: 
                        self.parent.project.timeline[item].visible = True
                    self.parent.project.updateViewSign.emit()
                self.update()
                self.parent.project.updateViewSign.emit()
        elif (event.type() == QtCore.QEvent.MouseButtonDblClick and
                       event.button()==QtCore.Qt.LeftButton):
            item = self.layerAt(event.y())
            if item is not None:
                self.parent.renameLayer(item)
                self.update()
        return QtGui.QWidget.event(self, event)
    
    def layerAt(self, y):
        l = (y - 23) // 20
        if 0 <= l < len(self.parent.project.timeline):
            return l
            
        
class TimelineCanvas(QtGui.QWidget):
    """ widget containing the timeline """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        self.grey = QtGui.QBrush(QtGui.QColor(0, 0, 0, 30))
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
        p.fillRect (0, 0, self.width(), self.height(), self.grey)
        p.fillRect (0, 0, self.width(), 21, self.white)
        p.drawLine (0, 21, self.width(), 21)
        for j, i in enumerate(range(7, self.width(), fW), 1):
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
        p.drawLine(self.parent.project.curFrame*fW, 0, 
                   self.parent.project.curFrame*fW, self.height())
        p.drawLine(self.parent.project.curFrame*fW + fW , 0, 
                   self.parent.project.curFrame*fW + fW , self.height())
        framesRects = []
        strechRects = []
        self.strechBoxList = []
        for y, layer in enumerate(self.parent.project.timeline):
            self.strechBoxList.append([])
            for x, frame in enumerate(layer):
                if frame:
                    w, h = 9, 17
                    s = x
                    while s+1 < len(layer) and not layer[s+1]:
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
        minH = (len(self.parent.project.timeline)*self.frameHeight) + self.margeY
        maxF = self.parent.project.timeline.frameCount()
        minW = (maxF * self.frameWidth) + self.margeX
        return (minW, minH)
        
    def event(self, event):
        if   (event.type() == QtCore.QEvent.MouseButtonPress and
              event.button()==QtCore.Qt.LeftButton):
            frame = self.frameAt(event.x())
            layer = self.layerAt(event.y())
            if frame is not None and layer is not None:
                strech = self.isInStrechBox(event.pos())
                if strech is not None:
                    self.strechFrame = (strech[1], frame, False)
                    self.parent.selection = False
                else:
                    self.parent.selection = [layer, frame, frame]
                    self.strechFrame = False
            else:
                self.strechFrame = False
                self.parent.selection = False
            self.parent.layersCanvas.update()
            self.update()
            self.parent.changeCurrent(frame, layer)
            return True
        elif (event.type() == QtCore.QEvent.MouseMove and
              event.buttons() == QtCore.Qt.LeftButton):
            frame = self.frameAt(event.x())
            layer = self.layerAt(event.y())
            if layer is not None and not self.strechFrame and not self.parent.selection:
                self.parent.project.curLayer = layer
            if frame is not None:
                if self.parent.selection:
                    self.parent.selection[2] = frame
                self.strech(frame)
            self.parent.layersCanvas.update()
            self.update()
            self.parent.changeCurrent(frame, layer)
            return True
        return QtGui.QWidget.event(self, event)
        
    def isInStrechBox(self, pos):
        for layer, i in enumerate(self.strechBoxList):
            for frame, j in enumerate(i):
                if j and j.contains(pos):
                    return (frame, layer)
        
    def strech(self, f):
        if self.strechFrame:
            sl, sf = self.strechFrame[0], self.strechFrame[1]
            if f == sf:
                return
            if not self.strechFrame[2]:
                self.parent.project.saveToUndo("frames")
            while f > sf:
                self.parent.project.timeline[sl].insert(sf+1, 0)
                sf += 1
            while f < sf:
                if not self.parent.project.timeline[sl][sf]:
                    self.parent.project.timeline[sl].pop(sf)
                    sf -= 1
                else:
                    break
            self.parent.adjustSize()
            self.strechFrame = (sl, sf, True)
        
    def frameAt(self, x):
        s = (x - self.margeX)  // self.frameWidth
        if 0 <= s <= self.width() // self.frameWidth:
            return s
        
    def layerAt(self, y):
        l = ((y - self.margeY) // self.frameHeight)
        if 0 <= l < len(self.parent.project.timeline):
            return l
        
        
class TimelineWidget(QtGui.QWidget):
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
        self.timelineV.resyzing.connect(self.adjustSize)
        
        self.layersV.verticalScrollBar().valueChanged.connect(
                lambda v: self.timelineV.verticalScrollBar().setValue(v))
        self.timelineV.verticalScrollBar().valueChanged.connect(
                lambda v: self.layersV.verticalScrollBar().setValue(v))
        self.project.updateTimelineSign.connect(self.timelineCanvas.update)
        self.project.updateTimelineSign.connect(self.layersCanvas.update)
        
        ### adding and deleting layers ###
        self.addLayerB = Button("add layer", "icons/layer_add.png", self.addLayerClicked)
        self.dupLayerB = Button("duplicate layer", "icons/layer_dup.png", self.duplicateLayerClicked)
        self.delLayerB = Button("delete layer", "icons/layer_del.png", self.deleteLayerClicked)
        self.mergeLayerB = Button("merge layer", "icons/layer_merge.png", self.mergeLayerClicked)
        self.upLayerB = Button("move up layer", "icons/layer_up.png", self.upLayerClicked)
        self.downLayerB = Button("move down layer", "icons/layer_down.png", self.downLayerClicked)
        
        ### adding and deleting images ###
        self.addFrameB = Button("add frame", "icons/frame_add.png", self.addFrameClicked)
        self.dupFrameB = Button("duplicate frame", "icons/frame_dup.png", self.duplicateFrameClicked)
        self.delFrameB = Button("delete frame", "icons/frame_del.png", self.deleteFrameClicked)
        self.clearFrameB = Button("clear frame", "icons/frame_clear.png", self.clearFrameClicked)
        
        ### ponionskin ###
        self.onionSkinPrevB = Button("onion skin - previous frame",
            "icons/onionskin_prev.png", self.onionskinPrevClicked, True)
        self.onionSkinNextB = Button("onion skin - next frame",
            "icons/onionskin_next.png", self.onionskinNextClicked, True)
            
        ### play the animation ###
        self.fpsW = QtGui.QSpinBox(self)
        self.fpsW.setValue(self.project.fps)
        self.fpsW.setRange(1, 60)
        self.fpsW.setSuffix(" fps")
        self.project.updateFpsSign.connect(lambda : self.fpsW.setValue(self.project.fps))
        self.fpsW.valueChanged.connect(self.fpsChanged)
        self.repeatB = Button("no repeat / repeat", "icons/play_no_repeat.png", self.repeatClicked)
        self.playFrameB = Button("play / pause", "icons/play_play.png", self.playPauseClicked)
        self.playFrameB.state = "play"

        ### layout ###
        layerTools = QtGui.QVBoxLayout()
        layerTools.setSpacing(0)
        layerTools.addWidget(self.addLayerB)
        layerTools.addWidget(self.dupLayerB)
        layerTools.addWidget(self.delLayerB)
        layerTools.addWidget(self.mergeLayerB)
        layerTools.addStretch()
        
        layerTools2 = QtGui.QHBoxLayout()
        layerTools2.setSpacing(0)
        layerTools2.addWidget(self.upLayerB)
        layerTools2.addWidget(self.downLayerB)
        
        canvasTools = QtGui.QHBoxLayout()
        canvasTools.setSpacing(0)
        canvasTools.addWidget(self.addFrameB)
        canvasTools.addWidget(self.dupFrameB)
        canvasTools.addWidget(self.delFrameB)
        canvasTools.addWidget(self.clearFrameB)
        canvasTools.addStretch()
        canvasTools.addWidget(self.onionSkinPrevB)
        canvasTools.addWidget(self.onionSkinNextB)
        canvasTools.addWidget(self.fpsW)
        canvasTools.addWidget(self.repeatB)
        canvasTools.addWidget(self.playFrameB)
        
        layout = QtGui.QGridLayout()
        layout.setSpacing(4)
        layout.addLayout(layerTools, 0, 0)
        layout.addWidget(self.layersV, 0, 1)
        layout.addWidget(self.timelineV, 0, 2)
        layout.addLayout(layerTools2, 1, 1)
        layout.addLayout(canvasTools, 1, 2)
        self.setLayout(layout)

    def changeCurrent(self, frame=None, layer=None):
        if not self.project.playing:
            if frame is not None:
                self.project.curFrame = frame
            if layer is not None:
                self.project.curLayer = layer
            if frame is not None or layer is not None:
                self.project.updateViewSign.emit()
            
    ######## Size adjust ###############################################
    def showEvent(self, event):
        self.timelineCanvas.setMinimumHeight(len(self.project.timeline)*20 + 25)
        self.timelineCanvas.update()
        self.layersCanvas.setMinimumHeight(self.timelineCanvas.height())
        self.layersCanvas.update()
        self.layersV.setViewportMargins(0, 0, 0, 
                    self.timelineV.horizontalScrollBar().height())
        self.layersV.setMinimumWidth(self.layersCanvas.width() + 
                    self.layersV.verticalScrollBar().width() + 2)
        self.layersV.setMaximumWidth(self.layersCanvas.width() + 
                    self.layersV.verticalScrollBar().width() + 2)
        
    def adjustSize(self, timeVSize=False):
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
        if self.selection:
            self.project.saveToUndo("frames")
            layer = self.project.timeline[self.selection[0]]
            f1, f2 = self.selection[1], self.selection[2]
            if f2 < f1:
                f1, f2, = f2, f1
            # copy frames
            self.toPaste = layer[f1:f2+1]
            # check if first frame is a real canvas
            if not self.toPaste[0]:
                self.toPaste[0] = layer.getCanvas(f1).copy_()
            # check if frame next to selection is a real canvas
            nex = layer.getCanvas(f2+1) 
            if nex and nex != layer.getCanvas(f1):
                layer[f2+1] = nex.copy_()
            # delete cutted frames
            del layer[f1:f2+1]
            self.timelineCanvas.update()
            
    def copy(self):
        if self.selection:
            layer = self.project.timeline[self.selection[0]]
            f1, f2 = self.selection[1], self.selection[2]
            if f2 < f1:
                f1, f2, = f2, f1
            # copy frames
            self.toPaste = layer[f1:f2+1]
            # check if first frame is a real canvas
            if not self.toPaste[0]:
                self.toPaste[0] = layer.getCanvas(f1).copy_()
            # make a real copy of all canvas
            for n, canvas in enumerate(self.toPaste):
                if canvas:
                    self.toPaste[n] = canvas.copy_()
        
    def paste(self):
        if self.toPaste:
            self.project.saveToUndo("frames")
            f = self.project.curFrame
            l = self.project.curLayer
            while f > len(self.project.timeline[l]):
                self.project.timeline[l].append(0)
            for n, canvas in enumerate(self.toPaste):
                self.project.timeline[l].insert(f+n, canvas)
            self.timelineCanvas.update()
            self.project.updateViewSign.emit()
            
    ######## Buttons ###################################################
    def addFrameClicked(self):
        self.project.saveToUndo("frames")
        layer = self.project.timeline[self.project.curLayer]
        layer.insertCanvas(self.project.curFrame, self.project.makeCanvas())
        self.adjustSize()
        self.project.updateViewSign.emit()
        
    def duplicateFrameClicked(self):
        self.project.saveToUndo("frames")
        layer = self.project.timeline[self.project.curLayer]
        layer.insertCanvas(self.project.curFrame, 
                           layer.getCanvas(self.project.curFrame).copy_())
        self.adjustSize()
        self.project.updateViewSign.emit()
        
    def deleteFrameClicked(self):
        self.project.saveToUndo("frames")
        layer = self.project.timeline[self.project.curLayer]
        frame = self.project.curFrame
        if frame >= len(layer):
            return
        if len(layer) == 1 and frame == 0:
            layer[frame].clear()
        elif layer[frame] and not frame + 1 >= len(layer) and not layer[frame + 1]:
            layer.pop(frame + 1)
        else:
            layer.pop(frame)
        self.adjustSize()
        self.project.updateViewSign.emit()
        
    def clearFrameClicked(self):
        f = self.project.timeline.getCanvas()
        if f:
            f.clear()
            self.project.updateViewSign.emit()
        
    def addLayerClicked(self):
        self.project.saveToUndo("frames")
        self.project.timeline.insert(self.project.curLayer, 
                                     self.project.makeLayer())
        self.adjustSize()
        self.project.updateViewSign.emit()
        
    def duplicateLayerClicked(self):
        self.project.saveToUndo("frames")
        layer = self.project.timeline[self.project.curLayer].deepCopy()
        layer.name = "%s copy" %(layer.name)
        self.project.timeline.insert(self.project.curLayer, layer)
        self.adjustSize()
        self.project.updateViewSign.emit()
        
    def deleteLayerClicked(self):
        self.project.saveToUndo("frames")
        del self.project.timeline[self.project.curLayer]
        self.project.curLayer = 0
        if not self.project.timeline:
            self.project.timeline.append(self.project.makeLayer())
        self.adjustSize()
        self.project.updateViewSign.emit()
        
    def mergeLayerClicked(self):
        if not self.project.curLayer < len(self.project.timeline) - 1:
            return
        self.project.saveToUndo("frames")
        layer1 = self.project.timeline[self.project.curLayer + 1]
        layer2 = self.project.timeline[self.project.curLayer]
        layer3 = self.project.makeLayer(False, True)
        layer3.name = layer1.name
        for i in range(max(len(layer1), len(layer2))):
            if i == len(layer1):
                layer3.append(layer2.getCanvas(i).copy_())
            elif i == len(layer2):
                layer3.append(layer1.getCanvas(i).copy_())
            elif i > len(layer1):
                if layer2[i]:
                    layer3.append(layer2[i].copy_())
                else:
                    layer3.append(0)
            elif i > len(layer2):
                if layer1[i]:
                    layer3.append(layer1[i].copy_())
                else:
                    layer3.append(0)
            elif layer1[i] or layer2[i]:
                c = layer1.getCanvas(i).copy_()
                c.mergeCanvas(layer2.getCanvas(i))
                layer3.append(c)
            else:
                layer3.append(0)
        del self.project.timeline[self.project.curLayer]
        self.project.timeline[self.project.curLayer] = layer3
        self.adjustSize()
        self.project.updateViewSign.emit()
        
    def upLayerClicked(self):
        self.project.saveToUndo("frames")
        l = self.project.curLayer
        f = self.project.timeline
        if l > 0:
            f[l], f[l-1] = f[l-1], f[l]
            self.project.curLayer = l - 1
            self.project.updateViewSign.emit()
            self.project.updateTimelineSign.emit()
        
    def downLayerClicked(self):
        self.project.saveToUndo("frames")
        l = self.project.curLayer
        f = self.project.timeline
        if l < len(f)-1:
            f[l], f[l+1] = f[l+1], f[l]
            self.project.curLayer = l + 1
            self.project.updateViewSign.emit()
            self.project.updateTimelineSign.emit()
    
    def renameLayer(self, l):
        name = self.project.timeline[l].name
        nName = RenameLayerDialog(name).getReturn()
        if nName:
            self.project.saveToUndo("frames")
            self.project.timeline[l].name = str(nName)
            self.project.updateTimelineSign.emit()

    ######## Onionskin #################################################
    def onionskinPrevClicked(self):
        self.project.onionSkinPrev = self.onionSkinPrevB.isChecked()
        self.project.updateViewSign.emit()

    def onionskinNextClicked(self):
        self.project.onionSkinNext = self.onionSkinNextB.isChecked()
        self.project.updateViewSign.emit()
        
    ######## Play ######################################################
    def fpsChanged(self):
        if 0 < self.fpsW.value() < 161:
            self.project.fps = self.fpsW.value()
            self.timelineCanvas.update()

    def repeatClicked(self):
        if self.project.loop:
            self.repeatB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_no_repeat.png")))
            self.project.loop = False
        else:
            self.repeatB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_repeat.png")))
            self.project.loop = True
        self.project.updateViewSign.emit()

    def playPauseClicked(self):
        """play the animation"""
        if self.playFrameB.state == 'play':
            self.playFrameB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_pause.png")))
            self.playFrameB.state = "stop"
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.animate)
            self.f = self.project.curFrame
            self.fps = self.project.fps
            self.project.playing = True
            maxF = max([len(l) for l in self.project.timeline])
            if self.project.curFrame+1 >= maxF:
                self.project.curFrame = 0
                self.timelineCanvas.update()
                self.project.updateViewSign.emit()
            self.timer.start(1000//self.fps)
        elif self.playFrameB.state == 'stop':
            self.playEnd()
            
    def playEnd(self):
        self.timer.stop()
        self.playFrameB.state = "play"
        self.playFrameB.setIcon(QtGui.QIcon(QtGui.QPixmap("icons/play_play.png")))
        self.project.playing = False
        self.project.updateViewSign.emit()
        
    def animate(self):
        if self.fps != self.project.fps:
            self.fps = self.project.fps
            self.timer.setInterval(1000//self.fps)
        maxF = max([len(l) for l in self.project.timeline])
        self.f = self.project.curFrame + 1
        if self.f < maxF:
            self.project.curFrame = self.f
            self.timelineCanvas.update()
            self.project.updateViewSign.emit()
        else:
            if self.project.loop:
                self.project.curFrame = 0
                self.timelineCanvas.update()
                self.project.updateViewSign.emit()
            else:
                self.playEnd()
            
