pixeditor
=========

a animated pixel art editor released under the GNU GPL V3

It is an alpha program, with bugs and limitation.  
You need python 3.x and PyQt to run it.

Shortcuts
------
Arrow key to move to previous / next frame / layer  
Space bar to play  
Ctrl Z / Ctrl Y to undo / redo  
Ctrl X / Ctrl C / Ctrl V to cut / copy / paste frames on the timeline  
Shift clic to draw lines  
Ctrl clic to select color  
Right clic to draw with alpha  

![alt screenshot](https://raw.github.com/pops/pixeditor/master/screenshot.png "screenshot")


install
======

Windows
------
First install python 3 :  
32 bit : http://www.python.org/ftp/python/3.3.2/python-3.3.2.msi  
or 64 bit : http://www.python.org/ftp/python/3.3.2/python-3.3.2.amd64.msi

Then install pyqt :  
32 bit : http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.10.3/PyQt4-4.10.3-gpl-Py3.3-Qt4.8.5-x32.exe  
or 64 bit : http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.10.3/PyQt4-4.10.3-gpl-Py3.3-Qt4.8.5-x64.exe

then download the program : https://github.com/pops/pixeditor/archive/master.zip  
extraxt the zip and run pixeditor.py  


Linux
----
just search Pyqt4 (python3-pyqt4) on the package manager, and install the version for python 3  
then download the program : https://github.com/pops/pixeditor/archive/master.zip  
make pixeditor.py executable and run it.  
You can install imagemagick to enable a gif export.  

in ubuntu : 

    sudo apt-get install python3-pyqt4 imagemagick  
    wget https://github.com/pops/pixeditor/archive/master.zip  
    unzip master.zip  
    cd pixeditor-master/  
    python3 pixeditor.py  


MacOs
----
It should work by installing python 3 an pyqt but apparently it didn't.  
Help is welcome.

