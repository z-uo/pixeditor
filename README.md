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


Install
======

Windows
------

Install the compiled verion here:
https://github.com/coco875/pixeditor/releases/tag/v0.1.1

First install python 3.7 :  
32 bit : https://www.python.org/ftp/python/3.7.0/python-3.7.0.exe  
or 64 bit : https://www.python.org/ftp/python/3.7.0/python-3.7.0-amd64.exe

Then install pyqt :  
first download : https://download.lfd.uci.edu/pythonlibs/x6hvwk7i/PyQt4-4.11.4-cp37-cp37m-win_amd64.whl
and execute in the same folder: `pip install PyQt4-4.11.4-cp37-cp37m-win_amd64.whl`

then download the program : https://github.com/pops/pixeditor/archive/master.zip  
or directly from the source
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

Buid
====

Windows
-----
install pyinstaller with `pip install pyinstaller`  
run : `pyinstaller --noconsole --onefile --hidden-import sip --distpath "dist/pixeleditor" --icon "icons/pixeditor.ico" pixeditor.py`
