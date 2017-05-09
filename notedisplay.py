# -*- coding: utf-8 -*-
# Copyright (C) 2013, Almar Klein
# BSD licensed.

""" notes.notedisplay
This module implements the widgets to view the notes.
"""

import os
import sys
import time
import datetime

from qtpy import QtCore, QtGui, QtWidgets


# CLR_NOTE = '#268bd2'
# CLR_TASK = '#cb4b16'  # orange '#cb4b16'   red '#dc322f'
# CLR_IDEA = '#859900'  # yellow '#b58900'   green '#859900'
# CLR_HIDE = '#666666'


class NotesContainer(QtWidgets.QWidget):
    """ A container for notes.
    """
    
    def __init__(self, parent, collection):
        self._main = parent
        super().__init__(parent)
        
        # Collection of kightweight note objects
        self._collection = collection
        
        # List of (heavy) widgets to display a note
        self._noteDisplays = []
        # List of (light) note objects
        self._notesToShow = []
        self._notesToShow_pending = []  # Notes are not shown yet
        
        # New note widget
        self._newnote = NewNoteDisplay(self)
        
        # Timer to keep scrolling right
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(100) # ms
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._onTimerTimeout)
        self._timer._focusWidget = None
        
        # Timer to keep add note displays if necessary
        self._stopperTimer = QtCore.QTimer(self)
        self._stopperTimer.setInterval(250) # ms
        self._stopperTimer.setSingleShot(False)
        self._stopperTimer.timeout.connect(self._checkNeedMoreDisplays)
        
        # Stopper widget
        self._stopper = QtWidgets.QLabel(self)
        self._stopper.setAlignment(QtCore.Qt.AlignTop)
        self._stopper.setMinimumHeight(100)
        self._stopperTimer.start()
        
        # Layout notes
        noteLayout = QtWidgets.QVBoxLayout(self)
        noteLayout.addWidget(self._newnote, 0)
        self.setLayout(noteLayout)
        #noteLayout.addStretch(1)
        noteLayout.addWidget(self._stopper, 1)
        noteLayout.setSpacing(0)  # Space between notes
        noteLayout.setContentsMargins(2,2,2,2) # Margins around list of notes
    
    
    def createNote(self):
        note = self._collection.newNote()
        noteDisplay = NoteDisplay(self, note)
        self._noteDisplays.append(noteDisplay)
        self.layout().insertWidget(1, noteDisplay, 0)
        noteDisplay.expandNote()
    
    
    def hasNotesExpanded(self):
        for noteDisplay in self._noteDisplays:
            if noteDisplay._editor and noteDisplay._editor.isVisible():
                return True
        else:
            return False
    
    
    def setCollection(self, collection):
        self._collection = collection
        self.showNotes()
    
    
    def showNotes(self):
        for noteDisplay in self._noteDisplays:
            noteDisplay.close()
        self._noteDisplays = []
        
        # Select notes and sort
        self._notesToShow = self._selectNotes()
        self._notesToShow_pending = list(self._notesToShow) # Copy
        self._showNotes()
    
    
    def currentSelection(self):
        """ Get more useful representation of what the user is looking for
        (prefix, tags, words).
        """
        # Get search items
        items = [i.strip().lower() for i in self._main._select.text().split(' ')]
        items = [i for i in items if i]
        
        prefix = ''
        tags = []
        words = []
        
        # First item can be the prefix
        if items and items[0] in '. % %% %%% ! !! !!! ? ?? ???':
            prefix = items.pop(0)
        
        # Next are either words or tags
        for item in items:
            if item.startswith('#'):
                tags.append(item)
            else:
                words.append(item)
        
        # Done
        return prefix, tags, words
        
    
    def _selectNotes(self):
        """ Turn notes visible or not, depending on the selection box.
        """
        # Get selection
        prefix, tags, words = self.currentSelection()
        
        # Collect tags
        self._allTags = allTags = set()
        self._selectedTags = selectedTags = set()
        
        # process prefix: Select all notes with the given prefix, or
        # select all but hidden notes
        selection1 = []
        if prefix:
            selection1 = [note for note in self._collection 
                                        if note.prefix.startswith(prefix)]
        else:
            selection1 = [note for note in self._collection 
                                        if note.prefix != '.']
        
        [allTags.update(n.tags) for n in selection1]
        
        # Search for tags and words
        if not (tags or words):
            selection2 = selection1
        else:
            selection2 = []
            for note in selection1:
                showNote = True
                for item in tags:
                    if item == '#':
                        if note.tags:
                            showNote = False
                    elif item not in note.tags:
                        showNote = False
                for item in words:
                    if item not in note.words:
                        showNote = False
                if showNote:
                    selection2.append(note)
        
        [selectedTags.update(n.tags) for n in selection2]
        
        # Update selection box
        self._main._tagsCompleter.setWords(allTags)
        #self._main._tagsCompleter.setWordsToIgnore(tags)
        
        # Sort
        selection2.sort(key=lambda x: x.created, reverse=True)
        if prefix:
            selection2.sort(key=lambda x: x.priority, reverse=True)
        return selection2
    
    
    def _showNotes(self):
        
        noteToFocus = None
        
        for i in range(16):
            if not self._notesToShow_pending:
                break
            
            note = self._notesToShow_pending.pop(0)
            
            noteDisplay = NoteDisplay(self, note)
            #self.layout().insertWidget(len(self._noteDisplays), noteDisplay, 0)
            self.layout().addWidget(noteDisplay, 0)
            self._noteDisplays.append(noteDisplay)
            noteToFocus = noteToFocus or noteDisplay
        
        self._stopper.setMinimumHeight(20*len(self._notesToShow_pending)+20)
        self.layout().addWidget(self._stopper, 1)
        
        if not self._notesToShow:
            self._stopper.setText('no notes to display')
        elif self._notesToShow_pending:
            self._stopper.setText('loading notes ...')
        else:
            self._stopper.setText('')
    
    
    def _checkNeedMoreDisplays(self):
        if self._notesToShow_pending:
            top = self._stopper.pos().y()  #self._stopper.rect().top()
            bottom = self.visibleRegion().boundingRect().bottom()
            if bottom > top:
                self._showNotes()
    
    
    def tags(self):
        """ Get tags grouped in two lists, one is a minimal set that
        contains all notes, the other contains the rest. Both lists
        have tags represented as tuples (tagname, count).
        """
        # Get selection
        selectedPrefix, selectedTags, selectedWords = self.currentSelection()
        
        # Create dict that maps tags to sets of notes.
        tagsDict = {}
        for note in self._notesToShow:
            for tag in note.tags:
                tagsDict.setdefault(tag, set()).add(note)
        
        # Sort tags by notecount
        tags = sorted(tagsDict.keys(), key=lambda t:len(tagsDict[t]), reverse=True)
        
        # Remove tags that we already selected for
        for tag in selectedTags:
            if tag in tags:
                tags.remove(tag)
        
        # Now for each tag, collect notes until we have all notes
        # Collect (estimate of) smallest set that contains all notes
        N = len(self._notesToShow)
        strictTags = []
        nonStrictTags = []
        allNotes = set()
        for tag in tags:
            if len(allNotes) < N:
                notesForTag = tagsDict[tag]
                if notesForTag.difference(allNotes):
                    allNotes = allNotes.union(notesForTag)
                    strictTags.append(tag)
                    continue
            nonStrictTags.append(tag)
        
        # Return the two lists
        return (    [(tag, len(tagsDict[tag])) for tag in strictTags],
                    [(tag, len(tagsDict[tag])) for tag in nonStrictTags]
                )
    
    def focusOnNote(self, widget):
        self._timer._focusWidget = widget
        self._timer.start()
    
    def _onTimerTimeout(self):
        widget = self._timer._focusWidget
        self._timer._focusWidget = None
        if widget:
            # Ensure whole widget is visible
            self._main._scrollArea.ensureWidgetVisible(widget)
            # If it is bigger than available screen, at least show the label
            if widget._editor and widget._editor.isVisible():
                self.focusOnEditor(widget._editor)
                #self._main._scrollArea.ensureWidgetVisible(widget._label)
    
    def focusOnEditor(self, editor):
        pos = editor.cursorRect().bottomLeft()
        pos = editor.mapTo(self, pos)
        self._main._scrollArea.ensureVisible(pos.x(), pos.y())



class NewNoteDisplay(QtWidgets.QPushButton):
    def __init__(self, parent):
        super().__init__(parent)
        
        #color = 'background-color:%s;' %  clr.name()
        border = 'border: 1px solid #aaa; border-radius: 5px;'
        self.setStyleSheet("NewNoteDisplay {%s}" % (border, ))
        self.setMinimumHeight(25)
        
        self.setText('new note')
        self.clicked.connect(self.parent().createNote)



class NoteDisplay(QtWidgets.QFrame):
    """ GUI representation of one note.
    """
    
    def __init__(self, parent, note):
        super().__init__(parent)
        self._note  = note
        
        # Create menu button
        self._but = QtWidgets.QToolButton(self)
        self._but.setPopupMode(self._but.InstantPopup)
        self._but.setStyleSheet(" QToolButton {border:none;}")
        # Create menu
        self._menu = QtWidgets.QMenu(self._but)
        self._menu.triggered.connect(self.onMenuSelect)
        self._but.setMenu(self._menu)
        # 
        # todo: move to default note file
        for actionName in ['Reset date', 'Hide note', 'Delete note (from current file)']:
            self._menu.addAction(actionName)
        
        # Create label
        self._label = QtWidgets.QLabel(self)
        self._label.mousePressEvent = lambda ev: self._collapseOrExpand()
        self._label.setWordWrap(True)
        
        # Create editor
        self._editor = None
        
        # Init
        self._layout()
        self.updateNote(note)
    
    
    def _layout(self):
        
        theLayout = QtWidgets.QVBoxLayout(self)
        theLayout.setContentsMargins(3,0,3,3)
        self.setLayout(theLayout)
        #
        butLayout = QtWidgets.QHBoxLayout(self._label)
        self._label.setLayout(butLayout)
        butLayout.addStretch(1)
        butLayout.addWidget(self._but, 0)
        #
        theLayout.setSpacing(1)
        theLayout.addWidget(self._label, 0)
    
    
    def onMenuSelect(self, action):
        actionText = action.text().lower()
        if 'hide' in actionText:
            self._note.setText('.' + self._note.text)
            self.close()
        elif 'delete' in actionText:
            self._note.delete()
            self.close()
        elif 'date' in actionText:
            default = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            default = self._note.createdStr or default
            res = QtWidgets.QInputDialog.getText(self, "Set date for this note",
                "Set the date for this note in format YYYY-MM-DD HH:MM (time is optional).",
                text=default)
            if isinstance(res, tuple):
                res = res[0]
            self._note.setCreatedStr(res)
            self.updateLabel()
            self._note.save(True)
    
    
    def updateNote(self, note):
        self._note = note
        if self._editor is not None:
            self._editor.setText(note.text)
        self.updateLabel()
    
    
    def updateLabel(self):
        note = self._note
        if self._editor is not None:
            note.setText(self._editor.toPlainText())
            self._tagsCompleter.setWordsToIgnore(note.tags)
        
        # Our background
        #MAP = {'%': CLR_NOTE, '!': CLR_TASK, '?': CLR_IDEA, '.': CLR_HIDE}
        from .app import config
        MAP = {'%': config['clr_note'], '!': config['clr_task'], 
               '?': config['clr_idea'], '.': config['clr_hide']}
        clr = QtGui.QColor(MAP.get(note.prefix[0], '#EEE'))
        clr = clr.lighter([100, 200, 180, 160][note.priority])
        color = 'background-color:%s;' %  clr.name()
        border = 'border: 1px solid #aaa; border-radius: 5px; margin-top:-1px;'
        self.setStyleSheet("NoteDisplay {%s%s}" % (border, color))
        
        # Get strings
        tagstring = ' '.join(note.tags) if note.tags else 'no tags'
        when = self._note.createdStr or 'no date'
        closeString = ' <span style="font-style:italic">(click to close&save)</span>'
        closeString = closeString if (self._editor and self._editor.isVisible()) else ''
        # Set text
        F = '<span style="font-size:small; color:#777;">%s - %s %s</span>'
        title = '<span style="font-family:mono;">%s</span> %s' % (
                        note.prefix, note.title.strip(note.prefix+' '))
        self._label.setText(F % (when, tagstring, closeString)+'<br />'+title)
        #self._title.setText(note.title)
    
    
    def makeEditor(self):
        if self._editor is None:
            self._editor = ScalingEditor(self)
            #
            from . import app
            self._tagsCompleter = app.TagCompleter(self._editor, self.parent()._allTags)
            self._editor.setCompleter(self._tagsCompleter)
            #
            self._editor.textChanged.connect(self.updateLabel)
            self.layout().addWidget(self._editor, 0)
            self._editor.setText(self._note.text)
            #self._editor.focusOutEvent = lambda ev: self._collapseOrExpand()
            
            
    
    def _collapseOrExpand(self):
        if self._editor and self._editor.isVisible():
            self.collapseNote()
        else:
            self.expandNote()
    
    def collapseNote(self):
        if self._editor is not None:
            self._editor.hide()
            #self._title.show()
            #self._note.setText(self._editor.toPlainText())
            self._note.save()
        self.updateLabel()
    
    def expandNote(self):
        self.makeEditor()
        self._editor.show()
        self._editor.setFocus()
        self._editor.moveCursor(QtGui.QTextCursor.Start, QtGui.QTextCursor.MoveAnchor)
        #self._title.hide()
        self.updateLabel()
        #self.parent().parent().parent().parent().focusOnNote(self)
        self.parent().focusOnNote(self)
        



class ScalingEditor(QtWidgets.QTextEdit):
    """ Editor that scales itself with its contents; scrolling takes
    place in the ScrollArea. Also implements autocompletion.
    """
    
    MINHEIGHT = 40
    MAXHEIGHT = 4000
    
    def __init__(self, parent):
        super().__init__()
        self._fitted_height = self.MINHEIGHT
        self.textChanged.connect(self._fitHeightToDocument)
        #self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.setAcceptRichText(False)
        self._completer = None
    
    def _fitHeightToDocument(self):
        self.document().setTextWidth(self.viewport().width())
        docSize = self.document().size().toSize()
        newHeight = docSize.height() + 5
        if newHeight != self._fitted_height:
            self._fitted_height = newHeight
            self.updateGeometry()
            self.parent().parent().updateGeometry()
            self.parent().parent().focusOnEditor(self)
    
    def resizeEvent(self, event):
        QtWidgets.QTextEdit.resizeEvent(self, event)
        self._fitHeightToDocument()
    
    def sizeHint(self):
        sizeHint = QtWidgets.QPlainTextEdit.sizeHint(self)
        sizeHint.setHeight(min(self.MAXHEIGHT, self._fitted_height))
        return sizeHint
    
    def minimumSizeHint(self):
        return QtCore.QSize(0, self.MINHEIGHT)
    
    def setCompleter(self, completer):
        if not completer: return
        completer.setWidget(self)
        completer.highlighted.connect(self._onCompletionHighlighted)
        self._completer = completer
    
    def _onCompletionHighlighted(self, text):
        # Start of word is right *after* the # symbol
        cursor = self.textCursor()
        cursor.movePosition(cursor.StartOfWord, cursor.KeepAnchor)
        cursor.insertText(text[1:])
    
    def textUnderCursor(self):
        cursor = self.textCursor()
        cursor.movePosition(cursor.StartOfLine, cursor.KeepAnchor)
        line = cursor.selectedText()
        line = line.replace(',', ' ').replace('  ', ' ').replace('  ', ' ')
        return line.split(' ')[-1]
    
    def keyPressEvent(self, event):
        QtWidgets.QTextEdit.keyPressEvent(self, event)
        
        completionPrefix = self.textUnderCursor()
        if (completionPrefix != self._completer.completionPrefix()):
            self._completer.setCompletionPrefix(completionPrefix)
            popup = self._completer.popup()
        
        # popup it up!
        cr = self.cursorRect()
        cr.setWidth(100)
        self._completer.complete(cr)
