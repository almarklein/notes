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

import os
import sys
import time
import datetime

from pyzolib import ssdf
from pyzolib.path import Path

from iep.codeeditor.qt import QtCore, QtGui
import iep


from .proxy import BaseNote, FileNotesProxy, NotesWorker


class Notes(QtGui.QWidget):
    """ Main class that implements a GUI interface to the notes.
    """
    
    removeNote = QtCore.Signal(str)
    addNote = QtCore.Signal(BaseNote)
    updateNote = QtCore.Signal(BaseNote)
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Store proxy
        self._notesProxy = FileNotesProxy('/home/almar/notes_test')
        #self._notesProxy = FileNotesProxy('/home/almar/Dropbox/home/notes')
        self._notesWorker = NotesWorker(self._notesProxy, self)
        
        # Create scroll area
        self._scrollArea = QtGui.QScrollArea(self)
        self._scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setFrameShape(self._scrollArea.NoFrame)
        
        # Create widget that will contain the notes
        self._container = QtGui.QWidget(self._scrollArea)
        self._scrollArea.setWidget(self._container)
        
        # Button to create a new note
        self._newNoteBut = QtGui.QToolButton(self)
        self._newNoteBut.setText('+')
        self._newNoteBut.clicked.connect(self.createNote)
        
        # Field to select contents
        self._select = LineEditWithToolButtons(self)
        self._select.setPlaceholderText('Select notes')
        self._select.editingFinished.connect(self.selectNotes)
        self._select.textChanged.connect(self.selectNotes)
        
        # Give select field a menu
        button = self._select.addButtonRight(None, False)
        menu = QtGui.QMenu(button)
        button.setMenu(menu)
        menu.triggered.connect(self.onMenuTriggered)
        #
        menu.addAction('! (select notes with tasks)')
        for tag in ['#foo', '#bar', '#home']:
            menu.addAction(tag)
        
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
        
        
        # Layout notes
        noteLayout = QtGui.QVBoxLayout(self._container)
        self._container.setLayout(noteLayout)
        noteLayout.addStretch(1)
        noteLayout.setSpacing(1)  # Space between notes
        noteLayout.setContentsMargins(2,2,2,2) # Margins around list of notes
        
        # Timer to keep scrolling right
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(100) # ms
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._onTimerTimeout)
        self._timer._focusWidget = None
        self._timer.start()
        
        # Signals
        self.removeNote.connect(self.onRemoveNote)
        self.addNote.connect(self.onAddNote)
        self.updateNote.connect(self.onUpdateNote)
        
        # Keep track of notes (NoteDisplay instances)
        self._notes = set()
        
#         for i in range(8):
#             self.createNote()
            
        # Start worker
        self._notesWorker.start()
    
    
    def onMenuTriggered(self, action):
        text = action.text().split(' ', 1)[0]
        curText = self._select.text().strip()
        if curText: curText += ' '
        self._select.setText( '%s%s ' % (curText, text) )
    
    def createNote(self):
        self._notesProxy.new_note()
    
    
    def onRemoveNote(self, id):
        for dNote in list(self._notes):
            if dNote.id() == id:
                dNote.close()
                self._notes.discard(dNote)
    
    
    def onAddNote(self, note):
        dNote = NoteDisplay(self._container, note)
        self._notes.add(dNote)
        
        # Insert in layout
        index = -1  # At the end
        layout = self._container.layout()
        for i in range(layout.count()-1, 0, -1):
            dNote2 = layout.itemAt(i).widget()
            if note.datetime() > dNote2._note.datetime():
                break
            else:
                index = i
        self._container.layout().insertWidget(index, dNote, 0)
        
        # Expand it?
        if not note.text():
            dNote.expandNote()
        
        # Focus on that widget
        self.focusOnNote(dNote)
    
    
    def onUpdateNote(self, note):
        id = note.id()
        for dNote in list(self._notes):
            if dNote.id() == id:
                dNote.updateNote(note)
    
    def focusOnNote(self, widget):
        self._timer._focusWidget = widget
        self._timer.start()
    
    def _onTimerTimeout(self):
        widget = self._timer._focusWidget
        self._timer._focusWidget = self._newNoteBut
        if widget:
            self._scrollArea.ensureWidgetVisible(widget)
    
    def closeEvent(self, event):
        #print('Closing Notes widget, stopping Notes worker.')
        super().closeEvent(event)
        self._notesWorker.stop()
    
    def selectNotes(self):
        """ Turn notes visible or not, depending on the selection box.
        """
        # Get search items
        items = [i.strip().lower() for i in self._select.text().split(' ')]
        items = [i for i in items if i]
        
        for dNote in self._notes:
            showNote = True
            for item in items:
                if item == '!':
                    if not dNote._tasks:
                        showNote = False
                elif item.startswith('#'):
                    if item == '#':
                        if dNote._tags:
                            showNote = False
                    elif item not in dNote._tags:
                        showNote = False
                else:
                    if item not in dNote._words:
                        showNote = False
            dNote.setVisible(showNote)



class NoteDisplay(QtGui.QFrame):
    """ GUI representation of one note.
    """
    
    def __init__(self, parent, note):
        super().__init__(parent)
        self._note  = note
        
        self.setStyleSheet(" NoteDisplay {background-color:#CCF; border-radius: 4px;  }")
        
        # Create menu button
        self._but = QtGui.QToolButton(self)
        self._menu = QtGui.QMenu(self._but)
        self._but.setMenu(self._menu)
        self._but.setIconSize(QtCore.QSize(8,8))
#         self._but.setStyleSheet(" QToolButton {padding:0px; margin:0px}")
        
        # Create label
        self._label = QtGui.QLabel(self)
        self._label.mousePressEvent = lambda ev: self._collapseOrExpand()
        self._label.setWordWrap(True)
        self._label.setStyleSheet(" QLabel {padding:0px; padding-left:3px; margin:0px;")
        self._label.setMaximumHeight(11)
        
        #self._label.mouseDoubleClickEvent = lambda ev: self._note.setText(self._editor.toPlainText())
        
        # Create title displat
        self._title = QtGui.QLabel(self)
        self._title.setStyleSheet(" QLabel {background-color:#FFF; padding: 2px; }")
        self._title.mousePressEvent = lambda ev: self._collapseOrExpand()
        
        # Create editor
        self._editor = None
        
        # Init
        self._layout()
        self.updateNote(note)
    
    
    def _layout(self):
        
        theLayout = QtGui.QVBoxLayout(self)
        theLayout.setContentsMargins(3,0,3,0)
        self.setLayout(theLayout)
        #
#         butLayout = QtGui.QVBoxLayout()
#         butLayout.setContentsMargins(0,0,0,0)
#         butLayout.addWidget(self._but, 0)
#         butLayout.addStretch(1)
        butLayout = QtGui.QHBoxLayout(self._label)
        self._label.setLayout(butLayout)
        butLayout.addStretch(1)
        butLayout.addWidget(self._but, 0)
        #
#         headerLayout = QtGui.QHBoxLayout()
#         headerLayout.setContentsMargins(10,0,3,0)
#         headerLayout.addWidget(self._label, 1)
#         headerLayout.addLayout(butLayout, 0)
        #
        #theLayout.addLayout(headerLayout, 0)
        theLayout.setSpacing(1)
        theLayout.addWidget(self._label, 0)
        theLayout.addWidget(self._title, 0)
        #theLayout.addWidget(self._editor, 0)
    
    
    def id(self):
        return self._note.id()
    
    
    def updateNote(self, note):
        #print(threading.current_thread())
        #return
        self._note = note
        if self._editor is not None:
            self._editor.setText(note.text())
        self.updateLabel()
    
    
    def updateLabel(self):
        self._parseText()
        # Get strings
        tagstring = ' '.join(self._tags) if self._tags else 'no tags'
        taskstring = '%i tasks'%len(self._tasks) if self._tasks else 'no tasks'
        when = self._note.datetime().strftime('%x')
        closeString = ' <span style="font-style:italic">(close to save)</span>'
        closeString = closeString if (self._editor and self._editor.isVisible() and self._editor.toPlainText() != self._note.text()) else ''
        # Set text
        F = '<span style="font-size:small; color:#777;">%s - %s - %s</span>'
        self._label.setText(F % (when, taskstring, tagstring))
        self._title.setText(self._titleText)
    
    
    def _parseText(self):
        
        # Get text
        if self._editor is None:
            text = self._note.text()
        else:
            text = self._editor.toPlainText()
        
        # Find title, tasks and tags
        title = ''
        tasks = []
        tags = set()
        words = set()
        for line in text.splitlines():
            if not title:
                title = line.strip()
            if line.startswith('! '):
                tasks.append(line)
            for word in line.split(' '):
                word = word.lower().strip()
                if word.startswith('#'):
                    if len(word) > 3 and word[1:].isalnum():
                        tags.add(word)
                elif word.isalnum():
                    words.add(word)
        
        # Cache this info
        self._titleText = title
        self._tasks = tasks
        self._tags = tags
        self._words = words
    
    def makeEditor(self):
        if self._editor is None:
            self._editor = ScalingEditor(self)
            self._editor.textChanged.connect(self.updateLabel)
            self.layout().addWidget(self._editor, 0)
            self._editor.setText(self._note.text())
    
    def _collapseOrExpand(self):
        if self._editor and self._editor.isVisible():
            self.collapseNote()
        else:
            self.expandNote()
    
    def collapseNote(self):
        if self._editor is not None:
            self._editor.hide()
            self._title.show()
            self._note.setText(self._editor.toPlainText())
        self.updateLabel()
    
    def expandNote(self):
        self.makeEditor()
        self._editor.show()
        self._title.hide()
        self.updateLabel()
        self.parent().parent().parent().parent().focusOnNote(self)



class ScalingEditor(QtGui.QTextEdit):
    """ Editor that scales itself with its contents; scrolling takes
    place in the ScrollArea.
    """
    
    MINHEIGHT = 40
    MAXHEIGHT = 400
    
    def __init__(self, parent):
        super().__init__()
        self._fitted_height = self.MINHEIGHT
        self.textChanged.connect(self._fitHeightToDocument)
        #self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
    
    def _fitHeightToDocument(self):
        self.document().setTextWidth(self.viewport().width())
        docSize = self.document().size().toSize()
        self._fitted_height = docSize.height() + 5
        self.updateGeometry()
        self.parent().parent().updateGeometry()
    
    def sizeHint(self):
        sizeHint = QtGui.QPlainTextEdit.sizeHint(self)
        sizeHint.setHeight(min(self.MAXHEIGHT, self._fitted_height))
        return sizeHint
    
    def minimumSizeHint(self):
        return QtCore.QSize(0, self.MINHEIGHT)
    

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
    