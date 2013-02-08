#!/usr/bin/env python
#-*- coding: utf-8 -*-

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt
import os

def open_pix(url=None):
    if not url:
        url = QtGui.QFileDialog.getOpenFileName(None, "open pix file", "", "Pix files (*.pix );;All files (*)")
    if url:
        try:
            save = open(url, "r")
            frames = []
            for line in save.readlines():
                if line[0:5] == "COLOR":
                    colors = [int(n) for n in line[6:-2].split(',')]
                elif line[0:5] == "SIZE ":
                    size = [int(n) for n in line[6:-2].split(',')]
                elif line[0:5] == "PIXEL":
                    frames.append([int(n) for n in line[6:-2].split(',')])
                elif line[0:5] == "STILL":
                    frames.append(None)
            save.close()
            return size, colors, frames
        except IOError:
            print "Can't open file"
            return False, False, False
    return False, False, False

def save_pix(size, color, frames, pixurl=None):
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
        col = [int(i) for i in color]
        save.write("COLOR%s\n" %(col))
        save.write("SIZE (%s, %s)\n" %(size[0], size[0]))
        for im in frames:
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
        return True
    except IOError:
        print "Can't open file"
        return False

def export_png(frames, url=None):
    url = QtGui.QFileDialog.getSaveFileName(None, "Export animation as png", "", "Png files (*.png )")
    if url:
        url = os.path.splitext(str(url))[0]
        files = []
        fnexist = False
        for n, im in enumerate(frames, 1):
            fn = "%s%s.png" %(url, n)
            if os.path.isfile(fn):
                fnexist = True
            if im:
                files.append((fn, im))
                sim = im
            else:
#                sim.save(fn)
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
