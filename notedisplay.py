
import os
import sys
import time
import datetime

from iep.codeeditor.qt import QtCore, QtGui


# from .noteproxy import Note
# from .notecollection import NoteCollection
# from .notedisplay import NoteContainer


class NotesContainer(QtGui.QWidget):
    """ A container for notes.
    """
    
    def __init__(self, parent, collection):
        self._main = parent
        super().__init__(parent)
        
        # Collection of kightweight note objects
        self._collection = collection
        
        # List of (heavy) widgets to display a note
        self._noteDisplays = []
        self._notesToShow = []
        
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
        self._stopper = QtGui.QWidget(self)
        self._stopper.setMinimumHeight(100)
        self._stopperTimer.start()
        
        # Layout notes
        noteLayout = QtGui.QVBoxLayout(self)
        self.setLayout(noteLayout)
        #noteLayout.addStretch(1)
        noteLayout.addWidget(self._stopper, 1)
        noteLayout.setSpacing(0)  # Space between notes
        noteLayout.setContentsMargins(2,2,2,2) # Margins around list of notes
    
    
    def createNote(self):
        note = self._collection.newNote()
        noteDisplay = NoteDisplay(self, note)
        self._noteDisplays.append(noteDisplay)
        self.layout().addWidget(noteDisplay, 0)
        noteDisplay.expandNote()
    
    
    def hasNotesExpanded(self):
        for noteDisplay in self._noteDisplays:
            if noteDisplay._editor and noteDisplay._editor.isVisible():
                return True
        else:
            return False
    
    
    def showNotes(self):
        for noteDisplay in self._noteDisplays:
            noteDisplay.close()
        self._noteDisplays = []
        
        # todo filter, sort
        # todo: only show a few
        
        # Select notes and sort
        self._notesToShow = self._selectNotes()
        self._showNotes()
    
    
    def _selectNotes(self):
        """ Turn notes visible or not, depending on the selection box.
        """
        # Get search items
        items = [i.strip().lower() for i in self._main._select.text().split(' ')]
        items = [i for i in items if i]
        
        notesToShow = []
        
        for note in self._collection:
            showNote = True
            for item in items:
                if item == '!':
                    if note.text.split(' ',1)[0] not in ['!', '!!', '!!!']:
                        showNote = False
                elif item == '!!':
                    if note.text.split(' ',1)[0] not in ['!!', '!!!']:
                        showNote = False
                elif item == '!!!':
                    if note.text.split(' ',1)[0] not in ['!!!']:
                        showNote = False
                elif item == '?':
                    if not note.text.startswith('?'):
                        showNote = False
                elif item.startswith('#'):
                    if item == '#':
                        if note.tags:
                            showNote = False
                    elif item not in note.tags:
                        showNote = False
                else:
                    if item not in note.words:
                        showNote = False
            if showNote:
                notesToShow.append(note)
        
        # Sort
        notesToShow.sort(key=lambda x: x.datetime, reverse=True)
        if '!' in items:
            notesToShow.sort(key=lambda x: x.priority, reverse=True)
        return notesToShow
    
    def _showNotes(self):
        
        noteToFocus = None
        
        for i in range(16):
            if not self._notesToShow:
                break
            
            note = self._notesToShow.pop(0)
            
            noteDisplay = NoteDisplay(self, note)
            self._noteDisplays.append(noteDisplay)
            self.layout().insertWidget(1, noteDisplay, 0)
            noteToFocus = noteToFocus or noteDisplay
            
#             # Insert in layout
#             index = -1  # At the end
#             layout = self.layout()
#             for i in range(layout.count()-1, 0, -1):
#                 noteDisplay2 = layout.itemAt(i).widget()
#                 if note.datetime > noteDisplay2._note.datetime:
#                     break
#                 else:
#                     index = i
#             self.layout().insertWidget(index, noteDisplay, 0)
        
        self._stopper.setMinimumHeight(20*len(self._notesToShow))
        # Focus on that widget
        self.focusOnNote(noteToFocus)
    
    
    def _checkNeedMoreDisplays(self):
        if self._notesToShow:
            bottom = self._stopper.rect().bottom()
            top = self.visibleRegion().boundingRect().top()
            if bottom > top:
                self._showNotes()
    
    
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
                pos = widget._editor.cursorRect().bottomLeft()
                pos = widget._editor.mapTo(self, pos)
                self._main._scrollArea.ensureVisible(pos.x(), pos.y())
                #self._main._scrollArea.ensureWidgetVisible(widget._label)



class NoteDisplay(QtGui.QFrame):
    """ GUI representation of one note.
    """
    
    def __init__(self, parent, note):
        super().__init__(parent)
        self._note  = note
        
        # Create menu button
        self._but = QtGui.QToolButton(self)
        self._but.setPopupMode(self._but.InstantPopup)
        self._but.setStyleSheet(" QToolButton {border:none;}")
        # Create menu
        self._menu = QtGui.QMenu(self._but)
        self._menu.triggered.connect(self.onMenuSelect)
        self._but.setMenu(self._menu)
        # 
        # todo: move to default note file
        for actionName in ['Delete note', 'Reset date']:
            self._menu.addAction(actionName)
        
        # Create label
        self._label = QtGui.QLabel(self)
        self._label.mousePressEvent = lambda ev: self._collapseOrExpand()
        self._label.setWordWrap(True)
        
        # Create editor
        self._editor = None
        
        # Init
        self._layout()
        self.updateNote(note)
    
    
    def _layout(self):
        
        theLayout = QtGui.QVBoxLayout(self)
        theLayout.setContentsMargins(3,0,3,3)
        self.setLayout(theLayout)
        #
        butLayout = QtGui.QHBoxLayout(self._label)
        self._label.setLayout(butLayout)
        butLayout.addStretch(1)
        butLayout.addWidget(self._but, 0)
        #
        theLayout.setSpacing(1)
        theLayout.addWidget(self._label, 0)
    
    
    def onMenuSelect(self, action):
        actionText = action.text().lower()
        if 'delete' in actionText:
            self._note.delete()
            self.close()
        elif 'date' in actionText:
            default = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            default = self._note.header or default
            res = QtGui.QInputDialog.getText(self, "Set date for this note",
                "Set the date for this note in format YYYY-MM-DD HH:MM (time is optional).",
                text=default)
            if isinstance(res, tuple):
                res = res[0]
            self._note.setHeader(res)
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
        
        # Our background
        MAP = {'!':'FCC', '!!':'FBB', '!!!':'FAA', 
                'x!': 'CCC',  'x!!':'CCC', 'x!!!':'CCC', 
                '?': 'DFD'}
        color = 'background-color:#%s;' %  MAP.get(note.text.split(' ',1)[0], 'DDF')
        border = 'border: 1px solid #aaa; border-radius: 5px; margin-top:-1px;'
        self.setStyleSheet("NoteDisplay {%s%s}" % (border, color))
        
        # Get strings
        tagstring = ' '.join(note.tags) if note.tags else 'no tags'
        when = self._note.datestr or 'no date'
        closeString = ' <span style="font-style:italic">(click to close&save)</span>'
        closeString = closeString if (self._editor and self._editor.isVisible()) else ''
        # Set text
        F = '<span style="font-size:small; color:#777;">%s - %s %s</span>'
        self._label.setText(F % (when, tagstring, closeString)+'<br />'+note.title)
        #self._title.setText(note.title)
    
    
    def makeEditor(self):
        if self._editor is None:
            self._editor = ScalingEditor(self)
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
        



class ScalingEditor(QtGui.QTextEdit):
    """ Editor that scales itself with its contents; scrolling takes
    place in the ScrollArea.
    """
    
    MINHEIGHT = 40
    MAXHEIGHT = 4000
    
    def __init__(self, parent):
        super().__init__()
        self._fitted_height = self.MINHEIGHT
        self.textChanged.connect(self._fitHeightToDocument)
        #self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        self.setAcceptRichText(False)
    
    def _fitHeightToDocument(self):
        self.document().setTextWidth(self.viewport().width())
        docSize = self.document().size().toSize()
        newHeight = docSize.height() + 5
        if newHeight != self._fitted_height:
            self._fitted_height = newHeight
            self.updateGeometry()
            self.parent().parent().updateGeometry()
    
    def resizeEvent(self, event):
        QtGui.QTextEdit.resizeEvent(self, event)
        self._fitHeightToDocument()
    
    def sizeHint(self):
        sizeHint = QtGui.QPlainTextEdit.sizeHint(self)
        sizeHint.setHeight(min(self.MAXHEIGHT, self._fitted_height))
        return sizeHint
    
    def minimumSizeHint(self):
        return QtCore.QSize(0, self.MINHEIGHT)
    

