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

DEFAUT_COLOR = 1
DEFAUT_SIZE = QtCore.QSize(64, 64)
DEFAUT_COLORTABLE = (QtGui.qRgba(0, 0, 0, 0), QtGui.qRgba(0, 0, 0, 255))
DEFAUT_PEN = ((0, 0),)
DEFAUT_TOOL = "pen"
        
class Project(QtCore.QObject):
    """ store all data that need to be saved"""
    update_view = QtCore.pyqtSignal()
    update_palette = QtCore.pyqtSignal()
    update_timeline = QtCore.pyqtSignal()
    updateBackground = QtCore.pyqtSignal()
    tool_changed = QtCore.pyqtSignal()
    pen_changed = QtCore.pyqtSignal()
    color_changed = QtCore.pyqtSignal()
    set_custom_pen = QtCore.pyqtSignal(list)
    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.undoList = []
        self.redoList = []
        self.pen = DEFAUT_PEN
        self.brush = lambda n : True
        self.tool = DEFAUT_TOOL
        self.fill_mode = "adjacent"
        self.select_mode = "cut"
        self.loop = False
        self.onionSkinPrev = False
        self.onionSkinNext = False
        self.init_project()
        
    def init_project(self, size=QtCore.QSize(DEFAUT_SIZE), frames=None, 
                     colorTable=list(DEFAUT_COLORTABLE), url=None):
        self.size = size
        self.colorTable = colorTable
        self.color = DEFAUT_COLOR
        if frames:
            self.timeline = Timeline(self, [Layer(self, layer["frames"], layer["name"]) for layer in frames])
        else:
            self.timeline = Timeline(self, [Layer(self, [self.make_canvas()], 'layer 1')])
        self.bg_color = QtGui.QColor(150, 150, 150)
        self.bg_pattern = 16
        self.url = url
        self.fps = 12
        self.curFrame = 0
        self.curLayer = 0
        self.playing = False
        self.importResources()
        
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
        
                     
    def set_color(self, color):
        self.color = color
        self.color_changed.emit()
        self.update_palette.emit()
        
    ######## undo/redo #################################################
    def save_to_undo(self, obj, save=False):
        if not save:
            doList = self.undoList
            self.redoList = []
        elif save == "redoList":
            doList = self.redoList
        elif save == "undoList":
            doList = self.undoList
        
        current = (self.curFrame, self.curLayer)
        if obj == "canvas":
            doList.append((obj, current, self.timeline.get_canvas().copy_()))
        elif obj == "frames":
            doList.append((obj, current, self.timeline.copy()))
        elif obj == "colorTable":
            doList.append((obj, current, list(self.colorTable)))
        elif obj == "size":
            doList.append((obj, current,(self.timeline.deep_copy(), 
                                         QtCore.QSize(self.size))))
        elif obj == "colorTable_frames":
            doList.append((obj, current, (self.timeline.deep_copy(), 
                                          list(self.colorTable))))
        elif obj == "timeline_canvas":
            doList.append((obj, current, self.timeline.deep_copy()))
        elif obj == "all":
            # no copy 
            doList.append((obj, current, (self.timeline, 
                                          self.colorTable, 
                                          self.size,
                                          QtGui.QColor(self.bg_color),
                                          self.bg_pattern,
                                          self.url,
                                          self.fps)))
        elif obj == "background":
            doList.append((obj, current, (QtGui.QColor(self.bg_color),
                                          self.bg_pattern)))
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
                self.save_to_undo("canvas", "redoList")
                canvas = self.timeline.get_canvas()
                canvas.swap(save)
            elif obj == "frames":
                self.save_to_undo("frames", "redoList")
                self.timeline = save
            elif obj == "colorTable":
                self.save_to_undo("colorTable", "redoList")
                self.colorTable = save
                for i in self.timeline.get_all_canvas():
                    i.setColorTable(self.colorTable)
            elif obj == "size":
                self.save_to_undo("size", "redoList")
                self.timeline = save[0]
                self.size = save[1]
            elif obj == "colorTable_frames":
                self.save_to_undo("colorTable_frames", "redoList")
                self.timeline = save[0]
                self.colorTable = save[1]
                for i in self.timeline.get_all_canvas():
                    i.setColorTable(self.colorTable)
            elif obj == "timeline_canvas":
                self.save_to_undo("timeline_canvas", "redoList")
                self.timeline = save
            elif obj == "all":
                self.save_to_undo("all", "redoList")
                self.timeline = save[0]
                self.colorTable = save[1]
                for i in self.timeline.get_all_canvas():
                    i.setColorTable(self.colorTable)
                self.size = save[2]
                self.bg_color = save[3]
                self.bg_pattern = save[4]
                self.updateBackground.emit()
                self.url = save[5]
                if self.url:
                    self.parent.setWindowTitle("pixeditor | %s" %(os.path.basename(self.url)))
                else:
                    self.parent.setWindowTitle("pixeditor")
                self.fps = save[6]
                self.parent.timelineWidget.fpsW.setText(str(self.fps))
            elif obj == "background":
                self.save_to_undo("background", "redoList")
                self.bg_color = save[0]
                self.bg_pattern = save[1]
                self.updateBackground.emit()
                
            self.update_view.emit()
            self.update_timeline.emit()
            self.update_palette.emit()

    def redo(self):
        if len(self.redoList) > 0:
            toRedo = self.redoList.pop(-1)
            obj = toRedo[0]
            current = toRedo[1]
            save = toRedo[2]
            self.curFrame = current[0]
            self.curLayer = current[1]
            if obj == "canvas":
                self.save_to_undo("canvas", "undoList")
                canvas = self.timeline.get_canvas()
                canvas.swap(save)
            elif obj == "frames":
                self.save_to_undo("frames", "undoList")
                self.timeline = save
            elif obj == "colorTable":
                self.save_to_undo("colorTable", "undoList")
                self.colorTable = save
                for i in self.timeline.get_all_canvas():
                    i.setColorTable(self.colorTable)
            elif obj == "size":
                self.save_to_undo("size", "undoList")
                self.timeline = save[0]
                self.size = save[1]
            elif obj == "colorTable_frames":
                self.save_to_undo("colorTable_frames", "undoList")
                self.timeline = save[0]
                self.colorTable = save[1]
                for i in self.timeline.get_all_canvas():
                    i.setColorTable(self.colorTable)
            elif obj == "timeline_canvas":
                self.save_to_undo("timeline_canvas", "undoList")
                self.timeline = save
            elif obj == "all":
                self.save_to_undo("all", "undolist")
                self.timeline = save[0]
                self.colorTable = save[1]
                for i in self.timeline.get_all_canvas():
                    i.setColorTable(self.colorTable)
                self.size = save[2]
                self.bg_color = save[3]
                self.bg_pattern = save[4]
                self.updateBackground.emit()
                self.url = save[5]
                if self.url:
                    self.parent.setWindowTitle("pixeditor | %s" %(os.path.basename(self.url)))
                else:
                    self.parent.setWindowTitle("pixeditor")
                self.fps = save[6]
                self.parent.timelineWidget.fpsW.setText(str(self.fps))
            elif obj == "background":
                self.save_to_undo("background", "undolist")
                self.bg_color = save[0]
                self.bg_pattern = save[1]
                self.updateBackground.emit()

            self.update_view.emit()
            self.update_timeline.emit()
            self.update_palette.emit()

    def make_canvas(self):
        """ make a new canvas
            or a copy of arg:canvas """
        return Canvas(self, self.size)

    def make_layer(self, layer=False, empty=False):
        """ make a new empty layer by default
            if arg:layer is a list : make a layer with it"""
        if empty:
            return Layer(self)
        name = "layer %s" %(len(self.timeline)+1)
        if not layer:
            return Layer(self, [self.make_canvas()], name)
        elif type(layer) == list:
            return Layer(self, layer, name)
            
    def get_alpha_color(self):
        return [index for index, color in enumerate(self.colorTable) if QtGui.QColor.fromRgba(color).alpha() == 0]
        
        
class Timeline(list):
    def __init__(self, project, layers):
        list.__init__(self, layers)
        self.project = project
        
    def copy(self):
        t = Timeline(self.project, [])
        for i in self:
            t.append(i.copy())
        return t
            
    def deep_copy(self):
        t = Timeline(self.project, [])
        for i in self:
            t.append(i.deep_copy())
        return t
        
    def get_canvas(self):
        """ return the current canvas """
        return self[self.project.curLayer].get_canvas(self.project.curFrame)

    def get_canvas_list(self, index):
        """ return the list of all canvas at a specific frame """
        return [layer.get_canvas(index) for layer in self]
                    
    def get_visible_canvas_list(self, index):
        """ return the list of all canvas at a specific frame """
        return [layer.get_canvas(index) for layer in self if layer.visible]
                    
    def get_visible_all_canvas(self):
        """ retrun all canvas """
        for l in self:
            if l.visible:
                for f in l:
                    if f:
                        yield f
                    
    def apply_to_all(self, function):
        for y, l in enumerate(self):
            for x, c in enumerate(l):
                if c:
                    self[y][x] = function(c)
                    
    def frame_count(self):
        return max([len(l) for l in self])
        
    def frame_visible_count(self):
        return max([len(l) for l in self if l.visible])
        
class Layer(list):
    def __init__(self, project, frames=None, name=''):
        if frames:
            list.__init__(self, frames)
        else:
            list.__init__(self)
        self.project = project
        self.name = name
        self.visible = True
                
    def copy(self):
        return Layer(self.project, self, self.name)
        
    def deep_copy(self):
        layer = Layer(self.project, self, self.name)
        for n, i in enumerate(layer):
            if i:
                layer[n] = layer[n].copy_()
        return layer
        
    def get_canvas(self, index):
        """ return the canvas at a specific frame """
        while 0 <= index < len(self):
            if self[index]:
                return self[index]
            else:
                index -= 1
        
        
class Canvas(QtGui.QImage):
    """ Canvas for drawing"""
    def __init__(self, project, arg, col=False):
        """ arg can be:
                a Canvas/QImage instance to be copied
                a url string to load the image
                a size tuple to create a new canvas """
        self.project = project
        if isinstance(arg, QtGui.QImage):
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
        for y in range(self.height()):
            for x in range(self.width()):
                l.append(self.pixelIndex(x, y))
        return l
    
    def return_as_matrix(self, rect):
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
        
    def merge_canvas(self, canvas, alpha=None):
        if alpha is None:
            alpha = self.project.get_alpha_color()
        for y in range(self.height()):
            for x in range(self.width()):
                col = canvas.pixelIndex(x, y)
                if col not in alpha:
                    self.setPixel(x, y, col)
        
    def merge_color(self, exCol, newCol):
        for y in range(self.height()):
            for x in range(self.width()):
                pixCol = self.pixelIndex(x, y)
                if pixCol == exCol:
                    self.setPixel(x, y, newCol)
                elif pixCol > exCol:
                     self.setPixel(x, y, pixCol-1)

    def swap_color(self, col1, col2):
        for y in range(self.height()):
            for x in range(self.width()):
                if self.pixelIndex(x, y) == col1:
                    self.setPixel(x, y, col2)
                elif self.pixelIndex(x, y) == col2:
                    self.setPixel(x, y, col1)
                    
    def replace_color(self, col1, col2):
        for y in range(self.height()):
            for x in range(self.width()):
                if self.pixelIndex(x, y) == col1:
                    self.setPixel(x, y, col2)
        
    def mix_colortable(self, colorTable):
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
        
    def sniff_colortable(self, colorTable):
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
        self.project.save_to_undo("canvas")
        self.fill(0)
    
    def draw_line(self, p2):
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
                self.draw_point(QtCore.QPoint(x, y))
        else:
            step = (p2.x()-p1.x()) / (p2.y()-p1.y() or 1)
            for i in range(disty):
                if p1.y() - p2.y() > 0:
                    i = -i
                y = p1.y() + i
                x = int(step * i + p1.x() + 0.5)
                self.draw_point(QtCore.QPoint(x, y))
        self.draw_point(p2)

    def draw_point(self, point):
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

    def flood_fill(self, point, col):
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
                
    def draw_rect(self, rect, color=None):
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
                self.project.set_color(self.pixelIndex(point))
                self.lastPoint = False
        elif self.project.tool == "pen":
            self.project.save_to_undo("canvas")
            if QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier and self.lastPoint:
                self.draw_line(point)
            else:
                self.draw_point(point)
            self.lastPoint = point
        elif (self.rect().contains(point) and self.project.tool == "fill" and 
              self.project.color != self.pixelIndex(point)):
            self.project.save_to_undo("canvas")
            if self.project.fill_mode == "adjacent":
                self.flood_fill(point, self.pixelIndex(point))
            elif self.project.fill_mode == "similar":
                self.replace_color(self.pixelIndex(point), self.project.color)
            self.lastPoint = False

    def move(self, point):
        if  (self.project.tool == "pipette" or
             (self.project.tool == "pen" or self.project.tool == "fill") and
             QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier):
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
