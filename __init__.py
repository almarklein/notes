# -*- coding: utf-8 -*-
# Copyright (C) 2012, the IEP development team
#
# IEP is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

tool_name = "Notes"
tool_summary = "Simple but powerful note taking app."

"""
A note has:
    name: id.seq
    id: uniquely identifies that note
    seq: sequence number for that note
    text: content

"""

# todo: overview of total+shown notes, number of tasks
# todo: creating new note is buggy
# todo: deleting a note is buggy
# todo: Collecy all used tags, and determine minimal set that covers all notes

import os
import sys
import time
import datetime

from pyzolib import ssdf
from pyzolib.path import Path

from iep.codeeditor.qt import QtCore, QtGui
import iep


from .noteproxy import Note
from .notecollection import NoteCollection
from .notedisplay import NotesContainer


class Notes(QtGui.QWidget):
    """ Main class that implements a GUI interface to the notes.
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Store proxy
        self._collection = NoteCollection(
                        '/home/almar/Dropbox/home/notes/notes.txt',
                        '/home/almar/Dropbox/home/notes/notes_dropbox.txt')
        
        # Create scroll area
        self._scrollArea = QtGui.QScrollArea(self)
        self._scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setFrameShape(self._scrollArea.NoFrame)
        
        # Create widget that will contain the notes
        self._container = NotesContainer(self, self._collection)
        self._scrollArea.setWidget(self._container)
        
        # Button to create a new note
        self._newNoteBut = QtGui.QToolButton(self)
        self._newNoteBut.setText('+')
        self._newNoteBut.clicked.connect(self._container.createNote)
        
        # Field to select contents
        self._select = LineEditWithToolButtons(self)
        self._select.setPlaceholderText('Select notes')
        self._select.editingFinished.connect(self._container.showNotes)
        self._select.textChanged.connect(self._container.showNotes)
        
        # Give select field a menu
        button = self._select.addButtonRight(None, False)
        menu = QtGui.QMenu(button)
        button.setMenu(menu)
        menu.triggered.connect(self.onMenuTriggered)
        #
        menu.addAction('! (select tasks)')
        menu.addAction('? (select ideas)')
        for tag in ['#Home', '#SA', '#Cybermind', '#Vispy', '#Cursus']:
            menu.addAction(tag)
        
        # Create timer to check for updates
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(2000) # ms
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self.checkUpToDate)
        self._timer.start()
        
        # Layout
        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self._scrollArea)
        layout.addWidget(self._newNoteBut)
        layout.setContentsMargins(0,0,0,0)
        #
        bottomLayout = QtGui.QHBoxLayout()
        bottomLayout.addWidget(self._newNoteBut, 0)
        bottomLayout.addWidget(self._select, 1)
        layout.addLayout(bottomLayout)
        
        self._container.showNotes()
    
    
    def onMenuTriggered(self, action):
        text = action.text().split(' ', 1)[0]
        curText = self._select.text().strip()
        if curText: curText += ' '
        self._select.setText( '%s%s ' % (curText, text) )
    
    
    def closeEvent(self, event):
        #print('Closing Notes widget, stopping Notes worker.')
        super().closeEvent(event)
        #self._notesWorker.stop()
        # todo: Need to stop it if I will use a worker again!
    
    
    def checkUpToDate(self):
        updatedFiles = self._collection.update()
        if updatedFiles:
            if not self._container.hasNotesExpanded():
                self._container.showNotes() # Update silently
            else:
                filestr = '\n'.join([repr(f) for f in updatedFiles])
                QtGui.QMessageBox.warning(self, "Notes updated externally",
                    "Notes have been updated externally in\n%s\n\n" % filestr +
                    "Saving your notes now may override these updates " +
                    "if they're defined in the same file." )


# From iep/tools/iepfilebrowser
class LineEditWithToolButtons(QtGui.QLineEdit):
    """ Line edit to which tool buttons (with icons) can be attached.
    """
    
    def __init__(self, parent):
        QtGui.QLineEdit.__init__(self, parent)
        self._leftButtons = []
        self._rightButtons = []
    
    def addButtonLeft(self, icon, willHaveMenu=False):
        return self._addButton(icon, willHaveMenu, self._leftButtons)
    
    def addButtonRight(self, icon, willHaveMenu=False):
        return self._addButton(icon, willHaveMenu, self._rightButtons)
    
    def _addButton(self, icon, willHaveMenu, L):
        # Create button
        button = QtGui.QToolButton(self)
        L.append(button)
        # Customize appearance
        if icon:
            button.setIcon(icon)
        button.setIconSize(QtCore.QSize(16,16))
        button.setStyleSheet("QToolButton { border: none; padding: 0px; }")        
        #button.setStyleSheet("QToolButton { border: none; padding: 0px; background-color:red;}");
        # Set behavior
        button.setCursor(QtCore.Qt.ArrowCursor)
        button.setPopupMode(button.InstantPopup)
        # Customize alignment
        if willHaveMenu:
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
            if sys.platform.startswith('win'):
                button.setText(' ')
        # Update self
        self._updateGeometry()
        return button
    
    def setButtonVisible(self, button, visible):
        for but in self._leftButtons:
            if but is button:
                but.setVisible(visible)
        for but in self._rightButtons:
            if but is button:
                but.setVisible(visible)
        self._updateGeometry()
    
    def resizeEvent(self, event):
        QtGui.QLineEdit.resizeEvent(self, event)
        self._updateGeometry(True)
    
    def showEvent(self, event):
        QtGui.QLineEdit.showEvent(self, event)
        self._updateGeometry()
    
    def _updateGeometry(self, light=False):
        if not self.isVisible():
            return
        
        # Init
        rect = self.rect()
        
        # Determine padding and height
        paddingLeft, paddingRight, height = 1, 1, 0
        #
        for but in self._leftButtons:
            if but.isVisible():
                sz = but.sizeHint()
                height = max(height, sz.height())
                but.move(   1+paddingLeft,
                            (rect.bottom() + 1 - sz.height())/2 )
                paddingLeft += sz.width() + 1
        #
        for but in self._rightButtons:
            if but.isVisible():
                sz = but.sizeHint()
                paddingRight += sz.width() + 1
                height = max(height, sz.height())
                but.move(   rect.right()-1-paddingRight, 
                            (rect.bottom() + 1 - sz.height())/2 )
        
        # Set padding
        ss = "QLineEdit { padding-left: %ipx; padding-right: %ipx} "
        self.setStyleSheet( ss % (paddingLeft, paddingRight) );
        
        # Set minimum size
        if not light:
            fw = QtGui.qApp.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
            msz = self.minimumSizeHint()
            w = max(msz.width(), paddingLeft + paddingRight + 10)
            h = max(msz.height(), height + fw*2 + 2)
            self.setMinimumSize(w,h)



if __name__ == '__main__':
    m = Notes(None)
    m.show()
    