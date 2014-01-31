# -*- coding: utf-8 -*-
# Copyright (C) 2013, Almar Klein
# BSD licensed.

""" notes.notecollection
This module specifies how notes from different sources are combined into
a collection.
"""

import os
import sys

from .noteproxy import FileProxy, Note


class NoteCollection:
    """ Represent a collection of notes. Handles the combining of multiple
    file proxies. 
    """ 
    def __init__(self, *filenames):
        
        # List of file proxies and set of notes contained therein
        self._fileProxies = []
        self._notes = {}
        mainProxy = None
        
        # Create proxies
        for filename in filenames:
            if not os.path.isfile(filename):
                raise ValueError('Note file does not exist: %r' % filename)
            newProxy = FileProxy(filename, mainProxy)
            self._fileProxies.append(newProxy)
            mainProxy = mainProxy or newProxy
        #if not self._fileProxies:
        #    raise RuntimeError('Need at least one note file.')
        
        # Query notes
        self.update()
    
    
    @classmethod
    def fromFolder(cls, folder, computername):
        if not os.path.isdir(folder):
            raise ValueError('The given note folder does not exist: %r' % folder)
        
        # Get main file, create if it does not yer exist
        mainfile = 'notes.%s.txt' % computername
        mainfile = os.path.normcase(os.path.join(folder, mainfile))
        if not os.path.isfile(mainfile):
            open(mainfile, 'wb')  # Touch to create empty file
        
        # Look for other files that we like
        files = [mainfile]
        for fname in os.listdir(folder):
            filename = os.path.normcase(os.path.join(folder,fname))
            if filename == mainfile:
                continue
            elif filename.count('.') >= 2 and filename.endswith('.txt'):
                files.append(filename)
        
        # Create collection
        return NoteCollection(*files)
    
    
    def __iter__(self):
        return self._notes.values().__iter__()
    
    def newNote(self):
        """ Create a new note in the default file.
        """
        note = self._fileProxies[0].newNote()
        self._notes[id] = note
        return note
    
    def update(self):
        updated = []
        for fileProxy in self._fileProxies:
            if fileProxy.hasChanged():
                updated.append(fileProxy._filename)
                #curNotes = fileProxy.currentNotes()
                newNotes = fileProxy.getNotes()
                for note in newNotes:
                    curNote = self._notes.get(note.id, None)
                    if curNote is None:
                        self._notes[note.id] = note
                    elif note.modifiedStr >= curNote.modifiedStr:
                        self._notes[note.id] = note
        return updated

