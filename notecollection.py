import os
import sys

from .noteproxy import FileProxy, Note


class NoteCollection:
    
    def __init__(self, *filenames):
        self._fileProxies = []
        self._notes = set()
        
        for filename in filenames:
            if not os.path.isfile(filename):
                raise ValueError('Note file does not exist: %r' % filename)
            self._fileProxies.append(FileProxy(filename))
        
        if not self._fileProxies:
            raise RuntimeError('Need at least one note file.')
        
        self.update()
    
    def __iter__(self):
        return self._notes.__iter__()
    
    def newNote(self):
        """ Create a new note in the default file.
        """
        note = self._fileProxies[0].newNote()
        self._notes.add(note)
        return note
    
    def update(self):
        updated = []
        for fileProxy in self._fileProxies:
            if fileProxy.hasChanged():
                updated.append(fileProxy._filename)
                curNotes = fileProxy.currentNotes()
                newNotes = fileProxy.getNotes()
                self._notes.difference_update(set(curNotes))
                self._notes.update(set(newNotes))
        return updated

