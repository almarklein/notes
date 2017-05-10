# -*- coding: utf-8 -*-
# Copyright (C) 2013, Almar Klein
# BSD licensed.

""" notes.app
This module implements the main application.
"""

import os
import sys
import json
import time
import datetime
from socket import gethostname

from qtpy import QtCore, QtGui, QtWidgets

from .noteproxy import Note
from .notecollection import NoteCollection
from .notedisplay import NotesContainer


# Taken from pyzolib
def appdata_dir(appname=None, roaming=False):
    """ appdata_dir(appname=None, roaming=False)
    Get the path to the application directory, where applications are allowed
    to write user specific files (e.g. configurations). For non-user specific
    data, consider using common_appdata_dir().
    If appname is given, a subdir is appended (and created if necessary). 
    If roaming is True, will prefer a roaming directory (Windows Vista/7).
    """
    
    # Define default user directory
    userDir = os.path.expanduser('~')
    
    # Get system app data dir
    path = None
    if sys.platform.startswith('win'):
        path1, path2 = os.getenv('LOCALAPPDATA'), os.getenv('APPDATA')
        path = (path2 or path1) if roaming else (path1 or path2)
    elif sys.platform.startswith('darwin'):
        path = os.path.join(userDir, 'Library', 'Application Support')
    # On Linux and as fallback
    if not (path and os.path.isdir(path)):
        path = userDir
    
    # Maybe we should store things local to the executable (in case of a 
    # portable distro or a frozen application that wants to be portable)
    prefix = sys.prefix
    if getattr(sys, 'frozen', None): # See application_dir() function
        prefix = os.path.abspath(os.path.dirname(sys.path[0]))
    for reldir in ('settings', '../settings'):
        localpath = os.path.abspath(os.path.join(prefix, reldir))
        if os.path.isdir(localpath):
            try:
                open(os.path.join(localpath, 'test.write'), 'wb').close()
                os.remove(os.path.join(localpath, 'test.write'))
            except IOError:
                pass # We cannot write in this directory
            else:
                path = localpath
                break
    
    # Get path specific for this app
    if appname:
        if path == userDir:
            appname = '.' + appname.lstrip('.') # Make it a hidden directory
        path = os.path.join(path, appname)
        if not os.path.isdir(path):
            os.mkdir(path)
    
    # Done
    return path


class Settings(object):
    """ Configuration for this app.
    """
    
    def __init__(self):
        
        # Determine filename to store config to
        dir = appdata_dir(roaming=True)
        self._filename = os.path.join(dir, '.notes_txt.json')
        
        # If used as a tool in Pyzo, use Pyzo config
        if 'pyzo' in sys.modules:
            import pyzo
            try:
                self._config = pyzo.config.tools.notes
                self._filename = None
            except AttributeError:
                pass
        
        # Load config or create new
        self._config = {}
        if self._filename:
            if os.path.isfile(self._filename):
                text = open(self._filename, 'rb').read().decode()
                if text.strip():
                    self._config = json.loads(text)
        # Apply defaults
        for name, value in [    ('notefolders', []),
                                ('notefolder', None),
                                ('fontsize', 11),
                                ('titlefont', 'Verdana'),
                                ('editfont', 'Dejavu sans mono'),
                                ('computername', gethostname()),
                                ('embedded', (self._filename is None)),
                                ('geometry', None),
                                ('clr_note', '#268bd2'),
                                ('clr_task', '#cb4b16'),
                                ('clr_idea', '#859900'),
                                ('clr_hide', '#666666'),
                            ]:
            if name not in self._config:
                self._config[name] = value
    
    
    def save(self):
        """ Save the configuration.
        """
        if self._filename:
            with open(self._filename, 'wb') as f:
                text = json.dumps(self._config)
                f.write(text.encode())


# Create config and save function
_settings = Settings()
config = _settings._config
saveConfig = _settings.save



class Notes(QtWidgets.QWidget):
    """ Main class that implements a GUI interface to the notes.
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Store proxy
        self._collection = NoteCollection()  # Init with empty collection
        
        # Create scroll area
        self._scrollArea = QtWidgets.QScrollArea(self)
        self._scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setFrameShape(self._scrollArea.NoFrame)
        
        # Create widget that will contain the notes
        self._container = NotesContainer(self, self._collection)
        self._scrollArea.setWidget(self._container)
        
        # Button to create a new note
        #self._newNoteBut = QtWidgets.QToolButton(self)
        #self._newNoteBut.setIcon(QtGui.QIcon.fromTheme('document-new'))
        #self._newNoteBut.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        #self._newNoteBut.clicked.connect(self._container.createNote)
        
        # Status label
        self._statusLabel = QtWidgets.QLabel(self)
        
        # Settings button
        self._settingsBut = QtWidgets.QToolButton(self)
        self._settingsBut.setText('Config ')
        #self._settingsBut.setIcon(QtGui.QIcon.fromTheme('emblem-system'))
        self._settingsBut.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self._settingsBut.setPopupMode(self._settingsBut.InstantPopup)
        #
        self._settingsMenu = QtWidgets.QMenu(self._settingsBut)
        self._settingsBut.setMenu(self._settingsMenu)
        self._settingsMenu.triggered.connect(self.onSettingsMenuTriggered)
        self._settingsMenu.aboutToShow.connect(self.onSettingsMenuAboutToShow)
        
        # Field to select contents
        self._select = LineEditWithToolButtons(self)
        self._select.setPlaceholderText('Select notes')
        self._select.editingFinished.connect(self._container.showNotes)
        self._select.textChanged.connect(self._container.showNotes)
        #
        self._tagsCompleter = TagCompleter(self._select)
        self._select.setCompleter(self._tagsCompleter)
        
        # Give select field a menu
        button = self._select.addButtonRight(None, False)
        self._tagMenu = menu = QtWidgets.QMenu(button)
        button.setMenu(menu)
        menu.triggered.connect(self.onTagsMenuTriggered)
        menu.aboutToShow.connect(self.onTagsMenuAboutToShow)
        
        # Create timer to check for updates
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(2000) # ms
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self.checkUpToDate)
        self._timer.start()
        
        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)
        #
        bottomLayout = QtWidgets.QHBoxLayout()
        bottomLayout.addWidget(self._select, 1)
        bottomLayout.addWidget(self._statusLabel, 0)
        bottomLayout.addWidget(self._settingsBut, 0)
        layout.addLayout(bottomLayout)
        #
        layout.addWidget(self._scrollArea)
        
        # 
        if config['embedded']:
            layout.setContentsMargins(0,0,0,0)
        else:
            #layout.setContentsMargins(0,0,0,0)
            self.setWindowTitle('Notes.txt note and task manager')
            if config['geometry']:
                self.setGeometry(*config['geometry'])
            else:
                self.resize(500, 700)
        
        # Start ...
        if config['notefolder']:
            self.setNoteFolder(config['notefolder'])
        else:
            self._container.showNotes()
    
    
    def setNoteFolder(self, folder):
        """ Select a note folder.
        Create a collection object that manages all note files in that folder
        also set the collection on the note container object.
        """
        # Try getting collection, use dummy otherwise
        errtext = ''
        try:
            collection = NoteCollection.fromFolder(folder, config['computername'])
        except Exception as err:
            errtext = str(err)
            collection = NoteCollection()
        # Set collection
        self._collection = collection
        self._container.setCollection(collection)
        # Set error text?
        if errtext:
            self._container._stopper.setText(errtext)
        
    
    
    def onSettingsMenuAboutToShow(self):
        
        # Init
        menu = self._settingsMenu
        menu.clear()
        
        menu.addAction('Edit config file ...')
        menu.addAction('Font size ...')
        menu.addAction('Add notes folder ...')
        menu.addSeparator()
        for folder in config['notefolders']:
            action = menu.addAction('Use %s' % folder)
            action.setCheckable(True)
            if folder == config['notefolder']:
                action.setChecked(True)
    
    
    def onSettingsMenuTriggered(self, action):
        cmd = action.text().lower()
        
        if 'edit' in cmd and 'config' in cmd:
            # Edit the config using a text editor
            
            # Create dialog 
            d = QtWidgets.QDialog(self)
            d.setLayout(QtWidgets.QVBoxLayout(d))
            d.setMinimumSize(600, 400)
            # Text edit
            t = QtWidgets.QPlainTextEdit(d)
            d.layout().addWidget(t)
            t.setPlainText(json.dumps(config, indent=4))
            # Button
            b = QtWidgets.QPushButton('Done', d)
            d.layout().addWidget(b)
            b.clicked.connect(d.accept)
            
            # Run it and get output
            d.exec_()
            if d.result():
                text = t.toPlainText()
                s = json.loads(text)
                for key in s:
                    config[key] = s[key]
        
        elif 'font' in cmd and 'size' in cmd:
            i = QtWidgets.QInputDialog.getInt(self, 'Set font size', '',
                config['fontsize'], 6, 32) 
            if isinstance(i, tuple):
                i = i[0]
            config['fontsize'] = i
        
        elif 'add' in cmd and 'folder' in cmd:
            # Add a folder
            
            # Get folder
            s = QtWidgets.QFileDialog.getExistingDirectory(self, 
                'Select folder to store notes')
            if isinstance(s, tuple):
                s = s[0]
            
            # Process
            if s and os.path.isdir(s) and s not in config['notefolders']:
                config['notefolders'].append(s)
                config['notefolder'] = s
                self.setNoteFolder(config['notefolder'])
        
        elif 'use' in cmd:
            folder = action.text().split(' ', 1)[1]
            config['notefolder'] = folder
            self.setNoteFolder(config['notefolder'])
        
        # Save
        saveConfig()
        
    
    
    def onTagsMenuAboutToShow(self):
        # Get selection and tags
        prefix, tags, words = self._container.currentSelection()
        strictTags, nonStrictTags = self._container.tags()
        
        # Clear menu
        menu = self._tagMenu
        menu.clear()
        menu.addAction('Clear selection')
        
        # Set prefix
        submenu = menu.addMenu('Note type ...')
        for p in (  ' select all note types', '% (select regular notes)', 
                    '! (select tasks)', '? (select ideas)'):
            a = submenu.addAction(p)
            a.setCheckable(True)
            a.setChecked(p.split(' ')[0]==prefix)
        
        # Add tags
        submenu = menu.addMenu('Minimal tag set ...')
        for tag, count in strictTags:
            submenu.addAction('%s (%i)' % (tag, count))
        if not strictTags:
            a = submenu.addAction('No minimal tags')
            a.setEnabled(False)
        #
        submenu = menu.addMenu('More tags ...')
        for tag, count in nonStrictTags:
            submenu.addAction('%s (%i)' % (tag, count))
        if not nonStrictTags:
            a = submenu.addAction('No extra tags')
            a.setEnabled(False)
    
    def onTagsMenuTriggered(self, action):
        text = action.text().split(' ', 1)[0]
        curText = self._select.text().strip()
        if text.lower().startswith('clear'):
            self._select.setText('')
        elif text in '%!?': # also empty string
            curText = curText.lstrip('%!? ')
            if (curText and text): text += ' '
            self._select.setText( '%s%s ' % (text, curText) )
        elif text.lower().startswith('#'):
            if curText: curText += ' '
            self._select.setText( '%s%s ' % (curText, text) )
    
    
    def closeEvent(self, event):
        #print('Closing Notes widget.')
        g = self.geometry()
        config['geometry'] = g.left(), g.top(), g.width(), g.height()
        saveConfig()
        super().closeEvent(event)
    
    
    def checkUpToDate(self):
        
        # Status
        n_notes = len(self._collection)
        n_hidden = len([n for n in self._collection if n.prefix == '.'])
        self._statusLabel.setText('%i notes (+ %i hidden)' % (n_notes - n_hidden, n_hidden))
        
        # Update from the outside
        updatedFiles = self._collection.update()
        if updatedFiles:
            if not self._container.hasNotesExpanded():
                self._container.showNotes() # Update silently
            else:
                filestr = '\n'.join([repr(f) for f in updatedFiles])
                QtWidgets.QMessageBox.warning(self, "Notes updated externally",
                    "Notes have been updated externally in\n%s\n\n" % filestr +
                    "Saving your notes now may override these updates " +
                    "if they're defined in the same file." )



class TagCompleter(QtWidgets.QCompleter):
    """ Completer implementation used for adding tags to a task.
    """
    
    def __init__(self, parent, words=None, wordsToIgnore=None):
        QtWidgets.QCompleter.__init__(self, [], parent)
        self.setWidget(parent)
        self._widget = parent # For some reason widget() can segfault on cleanup
        
        self._words = words or set()
        self._wordsToIgnore = wordsToIgnore or set()
        
        self.setCompletionMode(self.PopupCompletion)
        self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        
        self._updateWordList()
    
    def setWords(self, words):
        self._words = set(words)
        self._updateWordList()
    
    def setWordsToIgnore(self, words):
        self._wordsToIgnore = set(words)
        self._updateWordList()
    
    def _updateWordList(self):
        words = self._words.difference(self._wordsToIgnore)
        self.model().setStringList(sorted(words))
    
    def splitPath(self, path):
        # Simply return last entry
        lastword = path.split(' ')[-1]
        if lastword.startswith('#'):
            return [lastword]
        else:
            # Fool completer that the completion is an unknown word
            return ['xxxxxxxxxxxxxxxx']


# From pyzo/tools/pyzofilebrowser
class LineEditWithToolButtons(QtWidgets.QLineEdit):
    """ Line edit to which tool buttons (with icons) can be attached.
    """
    
    def __init__(self, parent):
        QtWidgets.QLineEdit.__init__(self, parent)
        self._leftButtons = []
        self._rightButtons = []
    
    def addButtonLeft(self, icon, willHaveMenu=False):
        return self._addButton(icon, willHaveMenu, self._leftButtons)
    
    def addButtonRight(self, icon, willHaveMenu=False):
        return self._addButton(icon, willHaveMenu, self._rightButtons)
    
    def _addButton(self, icon, willHaveMenu, L):
        # Create button
        button = QtWidgets.QToolButton(self)
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
        QtWidgets.QLineEdit.resizeEvent(self, event)
        self._updateGeometry(True)
    
    def showEvent(self, event):
        QtWidgets.QLineEdit.showEvent(self, event)
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
            fw = QtWidgets.qApp.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
            msz = self.minimumSizeHint()
            w = max(msz.width(), paddingLeft + paddingRight + 10)
            h = max(msz.height(), height + fw*2 + 2)
            self.setMinimumSize(w,h)
