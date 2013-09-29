#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Python 3 Compatibility
from __future__ import division
from __future__ import print_function

import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt
import xml.etree.ElementTree as ET

class Project(QtCore.QObject):
    """ store all data that need to be saved"""
    updateViewSign = QtCore.pyqtSignal()
    updatePaletteSign = QtCore.pyqtSignal()
    updateTimelineSign = QtCore.pyqtSignal()
    updateTimelineSizeSign = QtCore.pyqtSignal()
    updateBackgroundSign = QtCore.pyqtSignal()
    updateFpsSign = QtCore.pyqtSignal()
    toolChangedSign = QtCore.pyqtSignal()
    penChangedSign = QtCore.pyqtSignal()
    colorChangedSign = QtCore.pyqtSignal()
    customPenSign = QtCore.pyqtSignal(list)
    updateTitleSign = QtCore.pyqtSignal()
    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.undoList = []
        self.redoList = []
        self.pen = ((0, 0),)
        self.brush = lambda n : True
        self.tool = "pen"
        self.fillMode = "adjacent"
        self.selectMode = "cut"
        self.loop = False
        self.onionSkinPrev = False
        self.onionSkinNext = False
        self.initProject()
        self.importResources()
        
    def initProject(self, size=QtCore.QSize(64, 64), colorTable=None, frames=None):
        self.size = size
        if colorTable:
            self.colorTable = colorTable
        else:
            self.colorTable = [QtGui.qRgba(0, 0, 0, 0), QtGui.qRgba(0, 0, 0, 255)]
        self.color = 1
        if frames:
            self.timeline = Timeline(self, [Layer(self, frames, 'import')])
        else:
            self.timeline = Timeline(self, [Layer(self, [self.makeCanvas()], 'layer 1')])
        self.bgColor = QtGui.QColor(150, 150, 150)
        self.bgPattern = 16
        self.url = None
        self.dirUrl = None
        self.fps = 12
        self.curFrame = 0
        self.curLayer = 0
        self.playing = False
        self.saved = True
        self.updateTimelineSizeSign.emit()
        
    def importXml(self, rootElem, url):
        self.url = url
        self.dirUrl = os.path.dirname(url)
        if rootElem.attrib["version"] == "0.2":
            return self.importXml02(rootElem)
        sizeElem = rootElem.find("size").attrib
        self.size = QtCore.QSize(int(sizeElem["width"]), int(sizeElem["height"]))
        bgElem = rootElem.find("background").attrib
        self.bgColor = QtGui.QColor(int(bgElem["color"]))
        self.bgPattern = bgElem["pattern"]
        if type(self.bgPattern) is str and not os.path.isfile(self.bgPattern): 
            self.bgPattern = 16
        self.fps = int(rootElem.find("fps").attrib["fps"])
        colorTableElem = rootElem.find("colortable").text
        self.colorTable = [int(n) for n in colorTableElem.split(',')]
        timelineElem = rootElem.find("timeline")
        self.timeline = Timeline(self, [])
        for layerElem in timelineElem:
            layer = Layer(self, [], str(layerElem.attrib["name"]), 
                          bool(int(layerElem.attrib["visible"])))
            for f in layerElem.itertext():
                if f == "0":
                    layer.append(False)
                else:
                    nf = Canvas(self, self.size, self.colorTable)
                    nf.loadFromList([int(n) for n in f.split(',')])
                    layer.append(nf)
            self.timeline.append(layer)
        self.saved = True
        self.updateTitleSign.emit()
        self.updateTimelineSizeSign.emit()
            
    def importXml02(self, rootElem):
        sizeElem = rootElem.find("size").attrib
        self.size = QtCore.QSize(int(sizeElem["width"]), int(sizeElem["height"]))
        colorTableElem = rootElem.find("colors").text
        self.colorTable = [int(n) for n in colorTableElem.split(',')]
        framesElem = rootElem.find("frames")
        self.timeline = Timeline(self, [])
        for layerElem in framesElem:
            layer = Layer(self, [], str(layerElem.attrib["name"]), True)
            for f in layerElem.itertext():
                if f == "0":
                    layer.append(False)
                else:
                    nf = Canvas(self, self.size, self.colorTable)
                    nf.loadFromList([int(n) for n in f.split(',')])
                    layer.append(nf)
            self.timeline.append(layer)
        self.saved = True
        self.updateTitleSign.emit()
        self.updateTimelineSizeSign.emit()
        
    def exportXml(self):
        rootElem = ET.Element("pix", version="0.3")
        ET.SubElement(rootElem, "size", 
                      width=str(self.size.width()), 
                      height=str(self.size.height()))
        ET.SubElement(rootElem, "background", 
                      color=str(self.bgColor.rgb()),
                      pattern=str(self.bgPattern))
        fpsElem = ET.SubElement(rootElem, "fps", fps=str(self.fps))
        colorTableElem = ET.SubElement(rootElem, "colortable")
        colorTableElem.text = ','.join(str(n) for n in self.colorTable)
        timelineElem = ET.SubElement(rootElem, "timeline")
        for layer in self.timeline:
            layerElem = ET.SubElement(timelineElem, "layer")
            layerElem.attrib["name"] = layer.name
            layerElem.attrib["visible"] = str(int(layer.visible))
            for frame in layer:
                frameElem = ET.SubElement(layerElem, "frame")
                if frame:
                    frameElem.text = ','.join(str(p) for p in frame.returnAsList())
                else:
                    frameElem.text = "0"
        return rootElem
    
    def importImg(self, size, colorTable, frames):
        self.timeline.applyToAllCanvas(
                lambda c: Canvas(self, c.copy(QtCore.QRect(QtCore.QPoint(0, 0), size)), colorTable)
                )
        self.size = size
        self.colorTable = colorTable
        self.timeline.append(Layer(self, frames, 'import'))
        self.updateTimelineSizeSign.emit()
        
    def importResources(self):
        # brush
        # not really sure about what i'm doing here...
        brushPath = os.path.join("resources", "brush")
        ls = os.listdir(brushPath)
        ls.sort()
        brushFiles = [f[:-3] for f in ls if f.endswith(".py")]
        if not brushPath in sys.path:
            sys.path[:0] = [brushPath]
        importedModules = []
        for i in brushFiles:
            importedModules.append(__import__(i))
            exec("%s = sys.modules[i]"%(i,))
        self.brushList = []
        self.brushDict = {}
        for i in importedModules:
            self.brushList.append((i.name, QtGui.QIcon(QtGui.QPixmap(os.path.join(brushPath, i.icon)))))
            self.brushDict[i.name] = i.function
        # pen
        penPath = os.path.join("resources", "pen")
        ls = os.listdir(penPath)
        ls.sort()
        penFiles = [f[:-3] for f in ls if f.endswith(".py")]
        if not penPath in sys.path:
            sys.path[:0] = [penPath]
        importedModules = []
        for i in penFiles:
            importedModules.append(__import__(i))
            exec("%s = sys.modules[i]"%(i,))
        self.penList = []
        self.penDict = {}
        for i in importedModules:
            self.penList.append((i.name, QtGui.QIcon(QtGui.QPixmap(os.path.join(penPath, i.icon)))))
            self.penDict[i.name] = i.pixelList
        
    def setColor(self, color):
        self.color = color
        self.colorChangedSign.emit()
        self.updatePaletteSign.emit()
        
    ######## undo/redo #################################################
    def saveToUndo(self, obj, save=False):
        if self.saved:
            self.saved = False
            self.updateTitleSign.emit()
            
        if not save:
            doList = self.undoList
            self.redoList = []
        elif save == "redoList":
            doList = self.redoList
        elif save == "undoList":
            doList = self.undoList
        
        current = (self.curFrame, self.curLayer)
        if obj == "canvas":
            doList.append((obj, current, self.timeline.getCanvas().copy_()))
        elif obj == "frames":
            doList.append((obj, current, self.timeline.copy()))
        elif obj == "colorTable":
            doList.append((obj, current, list(self.colorTable)))
        elif obj == "size":
            doList.append((obj, current,(self.timeline.copy(), 
                                         self.size)))
        elif obj == "colorTable_frames":
            doList.append((obj, current, (self.timeline.deepCopy(), 
                                          list(self.colorTable))))
        elif obj == "timeline_canvas":
            doList.append((obj, current, self.timeline.deepCopy()))
        elif obj == "all":
            # no copy 
            doList.append((obj, current, (self.timeline, 
                                          self.colorTable, 
                                          self.size,
                                          QtGui.QColor(self.bgColor),
                                          self.bgPattern,
                                          self.url,
                                          self.fps)))
        elif obj == "background":
            doList.append((obj, current, (QtGui.QColor(self.bgColor),
                                          self.bgPattern)))
        if len(doList) > 50:
            doList.pop(0)

    def undo(self):
        if len(self.undoList) > 0:
            toUndo = self.undoList.pop(-1)
            obj = toUndo[0]
            current = toUndo[1]
            save = toUndo[2]
            self.curFrame = current[0]
            self.curLayer = current[1]
            if obj == "canvas":
                self.saveToUndo("canvas", "redoList")
                canvas = self.timeline.getCanvas()
                canvas.swap(save)
            elif obj == "frames":
                self.saveToUndo("frames", "redoList")
                self.timeline = save
            elif obj == "colorTable":
                self.saveToUndo("colorTable", "redoList")
                self.colorTable = save
                for i in self.timeline.getAllCanvas():
                    i.setColorTable(self.colorTable)
            elif obj == "size":
                self.saveToUndo("size", "redoList")
                self.timeline = save[0]
                self.size = save[1]
            elif obj == "colorTable_frames":
                self.saveToUndo("colorTable_frames", "redoList")
                self.timeline = save[0]
                self.colorTable = save[1]
                for i in self.timeline.getAllCanvas():
                    i.setColorTable(self.colorTable)
            elif obj == "timeline_canvas":
                self.saveToUndo("timeline_canvas", "redoList")
                self.timeline = save
            elif obj == "all":
                self.saveToUndo("all", "redoList")
                self.timeline = save[0]
                self.colorTable = save[1]
                for i in self.timeline.getAllCanvas():
                    i.setColorTable(self.colorTable)
                self.size = save[2]
                self.bgColor = save[3]
                self.bgPattern = save[4]
                self.updateBackgroundSign.emit()
                self.url = save[5]
                self.fps = save[6]
                self.parent.timelineWidget.fpsW.setText(str(self.fps))
                self.updateTitleSign.emit()
            elif obj == "background":
                self.saveToUndo("background", "redoList")
                self.bgColor = save[0]
                self.bgPattern = save[1]
                self.updateBackgroundSign.emit()
                
            self.updateViewSign.emit()
            self.updateTimelineSign.emit()
            self.updateTimelineSizeSign.emit()
            self.updatePaletteSign.emit()

    def redo(self):
        if len(self.redoList) > 0:
            toRedo = self.redoList.pop(-1)
            obj = toRedo[0]
            current = toRedo[1]
            save = toRedo[2]
            self.curFrame = current[0]
            self.curLayer = current[1]
            if obj == "canvas":
                self.saveToUndo("canvas", "undoList")
                canvas = self.timeline.getCanvas()
                canvas.swap(save)
            elif obj == "frames":
                self.saveToUndo("frames", "undoList")
                self.timeline = save
            elif obj == "colorTable":
                self.saveToUndo("colorTable", "undoList")
                self.colorTable = save
                for i in self.timeline.getAllCanvas():
                    i.setColorTable(self.colorTable)
            elif obj == "size":
                self.saveToUndo("size", "undoList")
                self.timeline = save[0]
                self.size = save[1]
            elif obj == "colorTable_frames":
                self.saveToUndo("colorTable_frames", "undoList")
                self.timeline = save[0]
                self.colorTable = save[1]
                for i in self.timeline.getAllCanvas():
                    i.setColorTable(self.colorTable)
            elif obj == "timeline_canvas":
                self.saveToUndo("timeline_canvas", "undoList")
                self.timeline = save
            elif obj == "all":
                self.saveToUndo("all", "undolist")
                self.timeline = save[0]
                self.colorTable = save[1]
                for i in self.timeline.getAllCanvas():
                    i.setColorTable(self.colorTable)
                self.size = save[2]
                self.bgColor = save[3]
                self.bgPattern = save[4]
                self.updateBackgroundSign.emit()
                self.url = save[5]
                self.fps = save[6]
                self.parent.timelineWidget.fpsW.setText(str(self.fps))
                self.updateTitleSign.emit()
            elif obj == "background":
                self.saveToUndo("background", "undolist")
                self.bgColor = save[0]
                self.bgPattern = save[1]
                self.updateBackgroundSign.emit()

            self.updateViewSign.emit()
            self.updateTimelineSign.emit()
            self.updateTimelineSizeSign.emit()
            self.updatePaletteSign.emit()

    def makeCanvas(self):
        """ make a new canvas"""
        return Canvas(self, self.size)

    def makeLayer(self, layer=False, empty=False):
        """ make a new empty layer by default
            if arg:layer is a list : make a layer with it"""
        if empty:
            return Layer(self)
        name = "layer %s" %(len(self.timeline)+1)
        if not layer:
            return Layer(self, [self.makeCanvas()], name)
        elif type(layer) == list:
            return Layer(self, layer, name)
            
        
class Timeline(list):
    def __init__(self, project, layers=[]):
        list.__init__(self, layers)
        self.project = project
        
    def copy(self):
        t = Timeline(self.project, [])
        for i in self:
            t.append(i.copy())
        return t
            
    def deepCopy(self):
        t = Timeline(self.project, [])
        for i in self:
            t.append(i.deepCopy())
        return t
        
    def getCanvas(self):
        """ return the current canvas """
        return self[self.project.curLayer].getCanvas(self.project.curFrame)

    def getCanvasList(self, index):
        """ return the list of all canvas at a specific frame """
        return [layer.getCanvas(index) for layer in self]
                    
    def getVisibleCanvasList(self, index):
        """ return the list of all canvas at a specific frame """
        return [layer.getCanvas(index) for layer in self if layer.visible]
                    
    def getAllCanvas(self):
        """ retrun all canvas """
        for l in self:
            for f in l:
                if f:
                    yield f
                    
    def applyToAllCanvas(self, function):
        for y, l in enumerate(self):
            for x, c in enumerate(l):
                if c:
                    self[y][x] = function(c)
                    
    def frameCount(self):
        return max([len(l) for l in self])
        
    def frameVisibleCount(self):
        return max([len(l) for l in self if l.visible])
        
class Layer(list):
    def __init__(self, project, frames=[], name='', visible=True):
        list.__init__(self, frames)
        self.project = project
        self.name = name
        self.visible = visible
                
    def copy(self):
        return Layer(self.project, self, self.name)
        
    def deepCopy(self):
        layer = Layer(self.project, self, self.name)
        for n, i in enumerate(layer):
            if i:
                layer[n] = layer[n].copy_()
        return layer
        
    def getCanvas(self, index):
        """ return the canvas at a specific frame """
        while 0 <= index < len(self):
            if self[index]:
                return self[index]
            else:
                index -= 1
        
    def insertCanvas(self, frame, canvas):
        if frame is None:
            frame = self.project.curFrame
        while frame >= len(self):
            self.append(0)
        if self[frame]:
            self.insert(frame, canvas)
        else:
            self[frame] = canvas
        
class Canvas(QtGui.QImage):
    """ Canvas for drawing"""
    def __init__(self, project, arg, col=False):
        """ arg can be:
                a Canvas/QImage instance to be copied
                a url string to load the image
                a size tuple to create a new canvas """
        self.project = project
        if isinstance(arg, QtGui.QImage) and type(col) is list:
            QtGui.QImage.__init__(self, arg)
            self.setColorTable(self.project.colorTable)
        elif isinstance(arg, QtGui.QImage):
            QtGui.QImage.__init__(self, arg)
        elif type(arg) is str:
            QtGui.QImage.__init__(self)
            self.load(arg)
        elif isinstance(arg, QtCore.QSize) and type(col) is list:
            QtGui.QImage.__init__(self, arg, QtGui.QImage.Format_Indexed8)
            self.setColorTable(col)
            self.fill(0)
        elif isinstance(arg, QtCore.QSize):
            QtGui.QImage.__init__(self, arg, QtGui.QImage.Format_Indexed8)
            self.setColorTable(self.project.colorTable)
            self.fill(0)

        self.lastPoint = False

    ######## import/export #############################################
    def loadFromList(self, li, exWidth=None, offset=(0, 0)):
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

    def returnAsList(self):
        l = []
        for y in range(self.height()):
            for x in range(self.width()):
                l.append(self.pixelIndex(x, y))
        return l
    
    def returnAsMatrix(self, rect):
        l = []
        i = 0
        for y in range(max(rect.top(), 0), min(rect.bottom()+1, self.height())):
            l.append([])
            for x in range(max(rect.left(), 0), min(rect.right()+1, self.width())):
                l[i].append(self.pixelIndex(x, y))
            i += 1
        return l
        
    def copy_(self):
        return Canvas(self.project, self)
        
    def mergeCanvas(self, canvas):
        alpha = [i for i, c in enumerate(self.colorTable()) if QtGui.QColor.fromRgba(c).alpha() == 0]
        for y in range(self.height()):
            for x in range(self.width()):
                col = canvas.pixelIndex(x, y)
                if col not in alpha:
                    self.setPixel(x, y, col)
        
    def mergeColor(self, exCol, newCol):
        for y in range(self.height()):
            for x in range(self.width()):
                pixCol = self.pixelIndex(x, y)
                if pixCol == exCol:
                    self.setPixel(x, y, newCol)
                elif pixCol > exCol:
                     self.setPixel(x, y, pixCol-1)

    def swapColor(self, col1, col2):
        for y in range(self.height()):
            for x in range(self.width()):
                if self.pixelIndex(x, y) == col1:
                    self.setPixel(x, y, col2)
                elif self.pixelIndex(x, y) == col2:
                    self.setPixel(x, y, col1)
                    
    def replaceColor(self, col1, col2):
        for y in range(self.height()):
            for x in range(self.width()):
                if self.pixelIndex(x, y) == col1:
                    self.setPixel(x, y, col2)
        
    def mixColortable(self, colorTable):
        selfColorTable = self.colorTable()
        colorTable = list(colorTable)
        for n, i in enumerate(selfColorTable):
            if i in colorTable:
                p = colorTable.index(i)
                selfColorTable[n] = p
            else: 
                if len(colorTable) == 256:
                    return None
                selfColorTable[n] = len(colorTable)
                colorTable.append(i)
        self.setColorTable(colorTable)
        for y in range(self.height()):
            for x in range(self.width()):
                self.setPixel(x, y, selfColorTable[self.pixelIndex(x, y)])
        return colorTable
        
    def sniffColortable(self, colorTable):
        colorTable = list(colorTable)
        for y in range(self.height()):
            for x in range(self.width()):
                color = self.pixel(x, y)
                if color in colorTable:
                    continue
                elif len(colorTable) == 256:
                    return None
                colorTable.append(color)
        return colorTable

    ######## draw ######################################################
    def clear(self):
        self.project.saveToUndo("canvas")
        self.fill(0)
    
    def drawLine(self, p2):
        p1 = self.lastPoint
        # http://fr.wikipedia.org/wiki/Algorithme_de_trac%C3%A9_de_segment_de_Bresenham
        distx = abs(p2.x()-p1.x())
        disty = abs(p2.y()-p1.y())
        if distx > disty:
            step = (p2.y()-p1.y()) / (p2.x()-p1.x() or 1)
            for i in range(distx):
                if p1.x() - p2.x() > 0:
                    i = -i
                x = p1.x() + i
                y = int(step * i + p1.y() + 0.5)
                self.drawPoint(QtCore.QPoint(x, y))
        else:
            step = (p2.x()-p1.x()) / (p2.y()-p1.y() or 1)
            for i in range(disty):
                if p1.y() - p2.y() > 0:
                    i = -i
                y = p1.y() + i
                x = int(step * i + p1.x() + 0.5)
                self.drawPoint(QtCore.QPoint(x, y))
        self.drawPoint(p2)

    def drawPoint(self, point):
        if len(self.project.pen[0]) == 2:
            for i, j in self.project.pen:
                p = QtCore.QPoint(point.x()+i, point.y()+j)
                if self.rect().contains(p) and self.project.brush(p.x()+p.y()):
                    self.setPixel(p, self.project.color)
        elif len(self.project.pen[0]) == 3:
            nc = self.colorCount()
            for i, j, c in self.project.pen:
                if c < nc:
                    p = QtCore.QPoint(point.x()+i, point.y()+j)
                    if self.rect().contains(p):
                        self.setPixel(p, c)

    def floodFill(self, point, col):
        l = [(point.x(), point.y())]
        while l:
            p = l.pop(-1)
            x, y = p[0], p[1]
            if self.rect().contains(x, y) and self.pixelIndex(x, y) == col:
                if self.project.brush(x + y):
                    self.setPixel(QtCore.QPoint(x, y), self.project.color)
                l.append((x+1, y))
                l.append((x-1, y))
                l.append((x, y+1))
                l.append((x, y-1))
                
    def drawRect(self, rect, color=None):
        if color is None:
            color = self.project.color
        for y in range(max(rect.top(), 0), min(rect.bottom()+1, self.height())):
            for x in range(max(rect.left(), 0), min(rect.right()+1, self.width())):
                self.setPixel(x, y, color)
        
    def clic(self, point):
        if  (self.project.tool == "pipette" or
             (self.project.tool == "pen" or self.project.tool == "fill") and
             QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier):
            if self.rect().contains(point):
                self.project.setColor(self.pixelIndex(point))
                self.lastPoint = False
        elif self.project.tool == "pen":
            self.project.saveToUndo("canvas")
            if QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier and self.lastPoint:
                self.drawLine(point)
            else:
                self.drawPoint(point)
            self.lastPoint = point
        elif (self.rect().contains(point) and self.project.tool == "fill" and 
              self.project.color != self.pixelIndex(point)):
            self.project.saveToUndo("canvas")
            if self.project.fillMode == "adjacent":
                self.floodFill(point, self.pixelIndex(point))
            elif self.project.fillMode == "similar":
                self.replaceColor(self.pixelIndex(point), self.project.color)
            self.lastPoint = False

    def move(self, point):
        if  (self.project.tool == "pipette" or
             (self.project.tool == "pen" or self.project.tool == "fill") and
             QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier):
            if self.rect().contains(point):
                self.project.setColor(self.pixelIndex(point))
                self.lastPoint = False
        elif self.project.tool == "pen":
            if self.lastPoint:
                self.drawLine(point)
                self.lastPoint = point
            else:
                self.drawPoint(point)
                self.lastPoint = point
