#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Python 3 Compatibility
from __future__ import print_function
from platform import python_version_tuple
if int(python_version_tuple()[0]) >= 3:
    xrange = range

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt
import os
import xml.etree.ElementTree as ET


######## open ##########################################################
def open_pix(url=None):
    if not url:
        url = QtGui.QFileDialog.getOpenFileName(None, "open pix file", "", "Pix files (*.pix );;All files (*)")
    if url:
        try:
            save = open(url, "r")
            size, colors, frames = return_canvas(save)
            save.close()
            return size, colors, frames
        except IOError:
            print("Can't open file")
            return False, False, False
        return False, False, False
        
def return_canvas(save):
    saveElem = ET.parse(save).getroot()
    sizeElem = saveElem.find("size").attrib
    size = (int(sizeElem["width"]), int(sizeElem["height"]))
    colorsElem = saveElem.find("colors").text
    colors = [int(n) for n in colorsElem.split(',')]
    framesElem = saveElem.find("frames")
    frames = []
    for layerElem in framesElem:
        print(layerElem.attrib["name"])
        layer = {"frames": [], "name": str(layerElem.attrib["name"]), "pos" : 0, "visible" : True, "lock" : False}
        for f in layerElem.itertext():
            if f == "0":
                layer["frames"].append(False)
            else:
                layer["frames"].append([int(n) for n in f.split(',')])
        frames.append(layer)
    return size, colors, frames

######## save ##########################################################
def save_pix(project, pixurl=None):
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
                    pixurl = os.path.join(os.path.splitext(str(url))[0], ".pix")
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
    try:
        save = open(str(pixurl), "w")
        save.write(return_pix(project))
        save.close()
        return True
    except IOError:
        print("Can't open file")
        return False
        
def return_pix(project):
    saveElem = ET.Element("pix", version="0.2")
    sizeElem = ET.SubElement(saveElem, "size")
    sizeElem.attrib["width"] = str(project.size[0])
    sizeElem.attrib["height"] = str(project.size[1])
    colorElem = ET.SubElement(saveElem, "colors", lenght=str(len(project.colorTable)))
    colorElem.text = ','.join(str(n) for n in project.colorTable)
    framesElem = ET.SubElement(saveElem, "frames", lenght=str(len(project.frames)))
    for nl, layer in enumerate(project.frames):
        layerElem = ET.SubElement(framesElem, "layer%s" %(nl))
        layerElem.attrib["name"] = layer["name"]
        for nf, f in enumerate(layer["frames"]):
            fElem = ET.SubElement(layerElem, "f%s" %(nf))
            if not f:
                fElem.text = "0"
            else:
                fElem.text = ','.join(str(p) for p in f.return_as_list())
    if int(python_version_tuple()[0]) >= 3:
        return ET.tostring(saveElem, encoding="unicode")
    else:
        return ET.tostring(saveElem)
    
def return_old_pix(size, color, frames):
    saveElem = ET.Element("pix", version="0,1")
    sizeElem = ET.SubElement(saveElem, "size")
    sizeElem.attrib["width"] = str(size[0])
    sizeElem.attrib["height"] = str(size[1])
    colorElem = ET.SubElement(saveElem, "colors", lenght=str(len(color)))
    colorElem.text = ','.join(str(n) for n in color)
    framesElem = ET.SubElement(saveElem, "frames", lenght=str(len(frames)))
    for n, frame in enumerate(frames):
        f = ET.SubElement(framesElem, "f%s" %(n))
        if not frame:
            f.text = "0"
        else:
            l = []
            for y in xrange(frame.height()):
                for x in xrange(frame.width()):
                    l.append(frame.pixelIndex(x, y))
            f.text = ','.join(str(p) for p in l)
    return ET.tostring(saveElem)

######## export ########################################################
#~ def export_png_old(frames, url=None):
    #~ url = QtGui.QFileDialog.getSaveFileName(None, "Export animation as png", "", "Png files (*.png )")
    #~ if url:
        #~ url = os.path.splitext(str(url))[0]
        #~ files = []
        #~ fnexist = False
        #~ for n, im in enumerate(frames, 1):
            #~ fn = "%s%s.png" %(url, n)
            #~ if os.path.isfile(fn):
                #~ fnexist = True
            #~ if im:
                #~ files.append((fn, im))
                #~ sim = im
            #~ else:
#~ #                sim.save(fn)
                #~ files.append((fn, sim))
        #~ if fnexist:
            #~ message = QtGui.QMessageBox()
            #~ message.setWindowTitle("Overwrite?")
            #~ message.setText("Some filename allready exist.\nDo you want to overwrite them?");
            #~ message.setIcon(QtGui.QMessageBox.Warning)
            #~ message.addButton("Cancel", QtGui.QMessageBox.RejectRole)
            #~ message.addButton("Overwrite", QtGui.QMessageBox.AcceptRole)
            #~ ret = message.exec_();
            #~ if ret:
                #~ for i in files:
                    #~ i[1].save(i[0])
        #~ else:
            #~ for i in files:
                #~ i[1].save(i[0])

def export(project, url=None):
    # nanim requires google.protobuf, which is Python 2.x only
    if int(python_version_tuple()[0]) >= 3:
        url = QtGui.QFileDialog.getSaveFileName(
            None, "export (.png)", "", "PNG files (*.png)")
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

def export_png(project, url):
    url = os.path.splitext(str(url))[0]
    files = []
    fnexist = False
    for nl, layer in enumerate(project.frames, 1):
        for nf, im in enumerate(layer["frames"], 1):
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
    for layer in project.frames:
        for im in layer["frames"]:
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
            for y in xrange(im.height()):
                for x in xrange(im.width()):
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
    #~ ouverturexml
    open_pix("/media/donnees/programation/pixeditor/master/test.pix")
