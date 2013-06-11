import os
import sys
import datetime

class Note:
    """ Representation of a note plus convenience stuff such
    as getting tags etc.
    
    A note has the following properties:
      * header - the header without the '----', that may contain a date
      * datetime - datetime instance. dateless notes have a very old date
      * datestr - string representation of the date
      * text - the full text :)
      * title - the first line of the text, stripped. 
      * prefix - the prefix indicating the type of note
      * priority - len(prefix)
      * tags - set of tags present in this note (all lowercase)
      * words - set of words present in this note (all lowercase)
    
    """
   
    def __init__(self, fileProxy, header, text):
        self._fileProxy = fileProxy
        self._header = header  # Header without the '----'
        self._text = text
        self._text0 = text
        #
        self._parseHeader()
        self._parseText()
        
    # Direct properties
    
    @property
    def header(self):
        return self._header
    
    @property
    def text(self):
        return self._text
    
    def setText(self, text):
        self._text = text
        self._parseText()
    
    def setHeader(self, text):
        self._header = text.strip()
        self._parseHeader()
    
    # Derived properties
    
    @property    
    def datetime(self):
        """ Datetime representation of this note. Use for selection and sorting.
        """
        return self._dt
    
    @property    
    def datestr(self):
        """ Date string for this note.
        """
        return self._dts
    
    @property
    def priority(self):
        """ For tasks, the priority of the task/note/idea.
        """
        return len(self.prefix)
    
    # Management
    
    def save(self, force=False):
        """ Save if the contents have not been changed.
        """
        if force or (self._text0 != self._text):
            self._fileProxy.save()
    
    def delete(self):
        """ Delete the note.
        """
        self._fileProxy._notes.remove(self)
        self._fileProxy.save()
    
    # Private 
    
    def _parseHeader(self):
        header = self._header
        #self._dt = datetime.datetime.now() + datetime.timedelta(100) # Future
        self._dt = datetime.datetime(1, 1, 1) # Long ago :) (only for sorting)
        self._dts = ''
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y%m%d']:
            try:
                self._dt = datetime.datetime.strptime(header.strip(' \t\n\r-:'), fmt)
                self._dts = self._dt.strftime('%Y-%m-%d')#('%x')
                break
            except ValueError:
                pass
    
    def _parseText(self):
        
        # Find title, tasks and tags
        title = ''
        tasks = []
        tags = set()
        words = set()
        
        for line in self._text.splitlines():
            if not title:
                title = line.strip()
            for word in line.split(' '):
                word = word.lower().strip()
                if word.startswith('#'):
                    if len(word) >= 3 and word[1:].isalnum():
                        tags.add(word)
                elif word.isalnum():
                    words.add(word)
        
        # Cache this info
        self.title = title
        self.tags = tags
        self.words = words
        
        # Store prefix
        self.prefix = self.title.split(' ', 1)[0]
        if self.prefix.startswith('.'):
            self.prefix = '.'  # hidden
        elif not (self.prefix and self.prefix in '! !! !!! ? ?? ??? % % %%%'):
            self.prefix = '%'  # Default is a normal note


class FileProxy:
    """ Representation of a file containing notes. 
    This class is responsible for loading the notes from the file,
    saving the notes back to file, and keeping track of updates.
    """
    
    def __init__(self, filename):
        self._filename = filename
        self._modtime = 0
        self._notes = []
    
    def hasChanged(self):
        """ Get whether the file was changed from the outside.
        """
        return self._modtime != os.path.getmtime(self._filename)
    
    def currentNotes(self):
        return self._notes
    
    def getNotes(self):
        notes = []
        
        with open(self._filename, 'rb') as f:
            alltext = f.read().decode('utf-8', 'ignore')
            for text in alltext.split('\n----'):
                try:
                    header, text = text.split('\n', 1)
                except ValueError:
                    header, text = text, ''
                header = header.strip().strip('-')
                text = text.strip()
                if header or text: # Skip completely empty notes
                    notes.append(Note(self, header, text+'\n'))
        
        # Dome
        self._modtime = os.path.getmtime(self._filename)
        self._notes = notes
        return notes
    
    def newNote(self):
        """ Create a new note.
        """
        header = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        note = Note(self, header, '\n')
        self._notes.append(note)
        return note
        
    def save(self):
        with open(self._filename, 'wb') as f:
            for note in self._notes:
                fullheader = '\n---- %s\n' % note.header 
                f.write(fullheader.encode('utf-8'))
                f.write(note.text.encode('utf-8'))
        self._modtime = os.path.getmtime(self._filename)

