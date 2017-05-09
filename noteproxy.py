# -*- coding: utf-8 -*-
# Copyright (C) 2013, Almar Klein
# BSD licensed.

""" notes.noteproxy
This module implements how notes are read/written to file.
"""

import os
import sys
import datetime
import random
import hashlib


# def str_to_int(s):
#     """ Create an integer hash for the given string.
#     """
#     chars = hashlib.md5(s.encode('utf-8')).hexdigest()
#     bignum = eval('0x'+chars)
#     return bignum


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
    
    __slots__ = ['_fileProxy', '_header', '_text', '_text0', 
                'id', '_created', '_createdStr', '_modified', '_modifiedStr',
                'title', 'tags', 'words', 'prefix']
   
    def __init__(self, fileProxy, header, text):
        self._fileProxy = fileProxy
        self._header = header  # Header without the '----'
        self._text = text
        self._text0 = text
        #
        self._parseHeader()
        self._parseText()
    
#     def __eq__(self, other):
#         return self.id == other.id
#     
#     def __hash__(self):
#         return evalself.id
    
    # Direct properties
    
    @property
    def text(self):
        return self._text
    
    def setText(self, text):
        text = text.replace('\n----', '\n ----')
        self._text = text
        self._parseText()
    
    def setCreatedStr(self, text):
        self._createdStr = text
        self._generateHeader()
    
    def setModifiedStr(self, text):
        self._modifiedStr = text
        self._generateHeader()
    
    def _generateHeader(self):
        self._header = 'id:%s, c:%s, m:%s' % (
                        self.id, self._createdStr, self._modifiedStr)
        self._parseHeader()
    
    # Derived properties
    
    @property    
    def created(self):
        """ Datetime representation of this note. Use for selection and sorting.
        """
        return self._created
    
    @property    
    def createdStr(self):
        """ Date string for this note.
        """
        return self._createdStr
    
    @property    
    def modfied(self):
        """ Datetime representation of this note. Use for selection and sorting.
        """
        return self._modified
    
    @property    
    def modifiedStr(self):
        """ Date string for this note.
        """
        return self._modifiedStr
    
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
            # Set modified
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.setModifiedStr(now)
            # Get proxy to save to
            if self._fileProxy.mainPoxy:
                self._fileProxy = self._fileProxy.mainPoxy
                self._fileProxy._notes.append(self)
            # Save
            self._fileProxy.save()
    
    def delete(self):
        """ Delete the note.
        """
        self._fileProxy._notes.remove(self)
        self._fileProxy.save()
    
    # Private 
    
    def _parseHeader(self):
        header = self._header.strip(' \t\n\r-:')
        created = ''
        modified = ''
        id = None
        
        # Parse the header
        for part in header.split(','):
            key, colon, value = part.partition(':')
            key, value = key.strip(), value.strip()
            #
            if key == 'id':
                id = value
            elif key in ('c', 'created'):
                created = value
            elif key in ('m', 'modified'):
                modified = value
            elif part:
                created = part
        
        # Process id
        if id is None:
            if self._text.strip():
                #id = hash(self._text) # doh, Python 3 has hash randomizatipn :)
                id = hashlib.sha256(self._text.encode('utf-8')).hexdigest()
            else:
                print('created random id')
                #id = random.randint(-sys.maxsize, sys.maxsize)
                id = ''.join([random.choice('0123456789abcdef') for c in range(40)])
        self.id = id
        
        # Parse date and time for created
        self._created = datetime.datetime(9000, 1, 1) # In the future (only for sorting)
        self._createdStr = ''
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y%m%d']:
            try:
                self._created = datetime.datetime.strptime(created, fmt)
                self._createdStr = self._created.strftime('%Y-%m-%d')#('%x')
                break
            except ValueError:
                pass
        
         # Parse date and time for modified
        self._modified = self._created
        self._modifiedStr = ''
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y%m%d']:
            try:
                self._modified = datetime.datetime.strptime(modified, fmt)
                self._modifiedStr = self._modified.strftime('%Y-%m-%d %H:%M:%S')#('%x')
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
    
    def __init__(self, filename, mainPoxy=None):
        self.mainPoxy = mainPoxy
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
        
        # Done
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
                fullheader = '\n---- %s\n' % note._header 
                f.write(fullheader.encode('utf-8'))
                f.write(note.text.encode('utf-8'))
        self._modtime = os.path.getmtime(self._filename)

