#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Python 3 Compatibility
from __future__ import division
from __future__ import print_function
from platform import python_version_tuple

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt
import os
import xml.etree.ElementTree as ET

from data import Canvas

######## open ##########################################################
def open_pix(project):
    url = QtGui.QFileDialog.getOpenFileName(None, "open pix file", "", "Pix files (*.pix );;All files (*)")
    if url:
        try:
            save = open(url, "r")
            saveElem = ET.parse(save).getroot()
            if saveElem.attrib["version"] == "0.2":
                size, frames, colorTable = return_canvas_02(saveElem, project)
            save.close()
            return size, frames, colorTable, url
        except IOError:
            print("Can't open file")
            return False, False, False, False
    return False, False, False, False

def return_canvas_02(saveElem, project):
    sizeElem = saveElem.find("size").attrib
    size = QtCore.QSize(int(sizeElem["width"]), int(sizeElem["height"]))
    colorsElem = saveElem.find("colors").text
    colorTable = [int(n) for n in colorsElem.split(',')]
    framesElem = saveElem.find("frames")
    frames = []
    for layerElem in framesElem:
        layer = {"frames": [], "name": str(layerElem.attrib["name"])}
        for f in layerElem.itertext():
            if f == "0":
                layer["frames"].append(False)
            else:
                nf = Canvas(project, size, colorTable)
                nf.loadFromList([int(n) for n in f.split(',')])
                layer["frames"].append(nf)
        frames.append(layer)
    return size, frames, colorTable

######## save ##########################################################
def save_pix_as(project, pixurl=None):
    if not pixurl:
        directory = ""
        repeat = True
        while repeat:
            url = QtGui.QFileDialog.getSaveFileName(None, "save pix file", directory, "Pix files (*.pix )")
            if url:
                directory = os.path.dirname(str(url))
                ext = os.path.splitext(str(url))[1]
                if ext == ".pix":
                    pixurl = url
                    repeat = False
                else:
                    pixurl = os.path.splitext(str(url))[0] + ".pix"
                    if os.path.isfile(pixurl):
                        message = """It seems that you try to save as %s, unfortunaly, I can't do that.
I can save your animation as :
%s
but this file allready exit.
Should I overwrite it ?""" %(ext, pixurl)
                        okButton = "Overwrite"
                    else:
                        message = """It seems that you try to save as %s, unfortunaly, I can't do that.
Should I save your animation as :
%s ?""" %(ext, pixurl)
                        okButton = "Save"

                    messageBox = QtGui.QMessageBox()
                    messageBox.setWindowTitle("Oups !")
                    messageBox.setText(message);
                    messageBox.setIcon(QtGui.QMessageBox.Warning)
                    messageBox.addButton("Cancel", QtGui.QMessageBox.RejectRole)
                    messageBox.addButton(okButton, QtGui.QMessageBox.AcceptRole)
                    ret = messageBox.exec_();
                    if ret:
                        repeat = False
            else:
                return False
    return save_pix(project, str(pixurl))
    
def save_pix(project, url):
    try:
        save = open(url, "w")
        save.write(return_pix(project))
        save.close()
        print("saved")
        return url
    except IOError:
        print("Can't open file")
        return False

def return_pix(project):
    saveElem = ET.Element("pix", version="0.2")
    sizeElem = ET.SubElement(saveElem, "size")
    sizeElem.attrib["width"] = str(project.size.width())
    sizeElem.attrib["height"] = str(project.size.height())
    colorElem = ET.SubElement(saveElem, "colors", lenght=str(len(project.colorTable)))
    colorElem.text = ','.join(str(n) for n in project.colorTable)
    framesElem = ET.SubElement(saveElem, "frames", lenght=str(len(project.timeline)))
    for nl, layer in enumerate(project.timeline):
        layerElem = ET.SubElement(framesElem, "layer%s" %(nl))
        layerElem.attrib["name"] = layer.name
        for nf, f in enumerate(layer):
            fElem = ET.SubElement(layerElem, "f%s" %(nf))
            if not f:
                fElem.text = "0"
            else:
                fElem.text = ','.join(str(p) for p in f.returnAsList())
    if int(python_version_tuple()[0]) >= 3:
        return ET.tostring(saveElem, encoding="unicode")
    else:
        return ET.tostring(saveElem)

######## import ########################################################
def import_png(project):
    urls = QtGui.QFileDialog.getOpenFileNames(
        None, "Import PNG and GIF", "", "PNG and GIF files (*.png *.gif);;All files (*)")
    if not urls:
        return None, None, None
    imgs = []
    canceled = []
    colorTable = []
    size = QtCore.QSize(0, 0)
    # open all img get the colortable and max size 
    canvasList = []
    for url in urls:
        if str(url).endswith("png") or str(url).endswith("PNG"):
            img = Canvas(project, str(url))
            canvasList.append((img, str(url)))
        elif str(url).endswith("gif") or str(url).endswith("GIF"):
            mov = QtGui.QMovie(str(url))
            for i in range(mov.frameCount()):
                mov.jumpToFrame(i)
                img = Canvas(project, mov.currentImage())
                canvasList.append((img, str(url)))
            
    for img, url in canvasList:
        if img.format() == QtGui.QImage.Format_Indexed8:
            colorMixed = img.mixColortable(colorTable)
            if colorMixed:
                colorTable = colorMixed
                imgs.append(img)
                size = size.expandedTo(img.size())
            else:
                canceled.append(url)
        else:
            colorMixed = img.sniffColortable(colorTable)
            if colorMixed:
                colorTable = colorMixed
                imgs.append(img)
                size = size.expandedTo(img.size())
            else:
                canceled.append(url)
    for n, img in enumerate(imgs):
        img = Canvas(project, img.convertToFormat(QtGui.QImage.Format_Indexed8, colorTable))
        if img.size() != size:
            li = img.returnAsList()
            width = img.width()
            img = Canvas(project, size, colorTable)
            img.loadFromList(li, width)
        imgs[n] = img
    
    if canceled:
        text = "Failed to import some non-indexed files :"
        for i in canceled:
            text = "%s\n %s" %(text, i)
        message = QtGui.QMessageBox()
        message.setWindowTitle("Import error")
        message.setText(text);
        message.setIcon(QtGui.QMessageBox.Warning)
        message.addButton("Ok", QtGui.QMessageBox.AcceptRole)
        message.exec_();
        
    return  size, imgs, colorTable

def export(project, url=None):
    # nanim requires google.protobuf, which is Python 2.x only
    if int(python_version_tuple()[0]) >= 3:
        url = QtGui.QFileDialog.getSaveFileName(
            None, "export (.png)", "", "PNG files (*.png)", QtGui.QFileDialog.DontConfirmOverwrite)
    else:
        url = QtGui.QFileDialog.getSaveFileName(
            None, "export (.png or .nanim)", "",
            "Png files (*.png);;Nanim files (*.nanim)")
    if url:
        # In Python 3.x, getSaveFileName returns a str, not a QString
        if str(url).endswith("png"):
            export_png(project, url)
        elif str(url).endswith("nanim"):
            export_nanim(project, url)

def export_png_all(project, url):
    url = os.path.splitext(str(url))[0]
    files = []
    fnexist = False
    for nl, layer in enumerate(project.timeline, 1):
        for nf, im in enumerate(layer, 1):
            fn = "%s%s%s.png" %(url, nl, nf)
            if os.path.isfile(fn):
                fnexist = True
            if im:
                files.append((fn, im))
                sim = im
            else:
                files.append((fn, sim))
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
    else:
        for i in files:
            i[1].save(i[0])
            

def export_png(project, fullUrl=""):
    isUrl = False
    while not isUrl:
        fullUrl = QtGui.QFileDialog.getSaveFileName(
                None, "export (.png)", fullUrl, "PNG files (*.png)", 
                QtGui.QFileDialog.DontConfirmOverwrite)
        if not fullUrl:
            return
        isUrl = True
        url = os.path.splitext(str(fullUrl))[0]
        nFrames = project.timeline.frameVisibleCount()
        for i in range(nFrames):
            fn = "%s%s%s.png" %(url, "0"*(len(str(nFrames))-len(str(i))), i)
            if os.path.isfile(fn):
                isUrl = False
                message = QtGui.QMessageBox()
                message.setWindowTitle("Overwrite?")
                message.setText("Some filename allready exist.\nDo you want to overwrite them?");
                message.setIcon(QtGui.QMessageBox.Warning)
                message.addButton("Cancel", QtGui.QMessageBox.RejectRole)
                message.addButton("Overwrite", QtGui.QMessageBox.AcceptRole)
                ret = message.exec_();
                if ret:
                    isUrl = True
                    break
                else:
                    isUrl = False
                    break
    for i in range(nFrames):
        fn = "%s%s%s.png" %(url, "0"*(len(str(nFrames))-len(str(i))), i)
        
        canvasList = project.timeline.getVisibleCanvasList(i)
        if len(canvasList) == 1:
            canvas = canvasList[0]
        else:
            canvas = QtGui.QImage(project.size, QtGui.QImage.Format_ARGB32)
            canvas.fill(QtGui.QColor(0, 0, 0, 0))
            p = QtGui.QPainter(canvas)
            for c in reversed(canvasList):
                if c:
                    p.drawImage(0, 0, c)
            p.end()
        canvas.save(fn)
        
    # convert all png to a gif with imagemagick
    os.system("convert -delay 1/12 -dispose Background -loop 0 %s*.png %s.gif" %(url, url))
    return fullUrl
        
def export_nanim(project, url):
    try:
        import google.protobuf
    except ImportError:
        message = QtGui.QMessageBox()
        message.setWindowTitle("Export error")
        # Set text format to rich text
        message.setTextFormat(1)
        message.setText("You need google protobuf to export as nanim.\nYou can download it at :\n<a href='https://code.google.com/p/protobuf/downloads/list'>https://code.google.com/p/protobuf/downloads/list</a>");
        message.setIcon(QtGui.QMessageBox.Warning)
        message.addButton("Ok", QtGui.QMessageBox.AcceptRole)
        message.exec_();
        return

    import nanim_pb2
    nanim = nanim_pb2.Nanim()
    animation = nanim.animations.add()
    animation.name = "default"
    i = 0
    for layer in project.timeline:
        for im in layer:
            if not im:
                im = exim
            exim = im
            nimage = nanim.images.add()
            nimage.width = im.width()
            nimage.height = im.height()
            nimage.format = nanim_pb2.RGBA_8888
            nimage.name = "img_%d" % i
            i = i + 1
            pixels = bytearray()
            for y in range(im.height()):
                for x in range(im.width()):
                    colors = QtGui.QColor(im.pixel(x,y))
                    pixels.append(colors.red())
                    pixels.append(colors.green())
                    pixels.append(colors.blue())
                    pixels.append(colors.alpha())
            nimage.pixels = str(pixels)

            frame = animation.frames.add()
            frame.imageName = nimage.name
            frame.duration = 100
            frame.u1 = 0
            frame.v1 = 0
            frame.u2 = 1
            frame.v2 = 1
    f = open(url, "wb")
    f.write(nanim.SerializeToString())
    f.close()

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    import_gif("/media/donnees/programation/pixeditor/dup.gif")
    sys.exit(app.exec_())
