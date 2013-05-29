import os
import sys
import time
import datetime
import threading


class NotesWorker(threading.Thread):
    """ Worker thread that periodically polls the notes proxy.
    Keeps track of a list of note names, and fired events at the given
    notesDisplay when a note is removed, added, or updated.
    """
    
    def __init__(self, notesProxy, notesDisplay):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        #
        self._notesProxy = notesProxy
        self._notesDisplay = notesDisplay
        #
        self._exit = False
        self._note_names = set()
    
    def stop(self):
        self._exit = True
    
    def run(self):
        time.sleep(0.2)
        try:
            try: 
                self._run()
            except Exception as err:
                if self._exit is None or os is None:
                    pass  # Shutting down ...
                else:
                    print('Exception in Notes worker ' + str(err))
        except Exception:
            pass  # Interpreter is shutting down
    
    def _run(self):
        
        while True:
            if self._exit:
                return
            time.sleep(1.0)
            if self._exit:
                return
            
            # Get new list of notes
            new_note_names = set(self._notesProxy.get_note_names())
            
            # Find names of added and removed notes
            names_to_rem = self._note_names.difference(new_note_names)
            names_to_add = new_note_names.difference(self._note_names)
            
            # Prepare for next round
            self._note_names = new_note_names
            
            # Get corresponding ids
            ids_of_names_to_rem = set([id.split('.')[0] for id in names_to_rem])
            ids_of_names_to_add = set([id.split('.')[0] for id in names_to_add])
            
            # Analyse: find ids of notes that need to be added, removed, or updated
            ids_to_rem, ids_to_add, ids_to_upd = {}, {}, {}
            for name in list(names_to_rem):
                id, seq = self._name_to_id_and_seq(name)
                if id in ids_of_names_to_add:
                    if ids_to_upd.get(id, -1) < seq:
                        ids_to_upd[id] = seq
                else:
                    if ids_to_rem.get(id, -1) < seq:
                        ids_to_rem[id] = seq
            for name in list(names_to_add):
                id, seq = self._name_to_id_and_seq(name)
                if id in ids_of_names_to_rem:
                    if ids_to_upd.get(id, -1) < seq:
                        ids_to_upd[id] = seq
                else:
                    if ids_to_add.get(id, -1) < seq:
                        ids_to_add[id] = seq
            
            # Process
            for id in ids_to_rem:
                self._notesDisplay.removeNote.emit(id)
                time.sleep(0.001)
            for id in ids_to_add:
                name = '%s.%i' % (id, ids_to_add[id])
                note = self._notesProxy.get_note(name)
                self._notesDisplay.addNote.emit(note)
                time.sleep(0.01)
            for id in ids_to_upd:
                name = '%s.%i' % (id, ids_to_upd[id])
                note = self._notesProxy.get_note(name)
                self._notesDisplay.updateNote.emit(note)
                time.sleep(0.01)
    
    def _name_to_id_and_seq(self, name):
        id, seq = name.split('.');
        try:
            seq = int(seq)
        except Exception:
            seq = 1
        return id, seq



class NotesProxy:
    def get_note_names(self):
        raise NotImplemented()
    def get_note(self, id):
        raise NotImplemented()
    def new_note(self):
        raise NotImplemented()


class FileNotesProxy(NotesProxy):
    def __init__(self, *dirs):
        self._dirs = dirs
    
    def get_note_names(self):
        names = set()
        for dir in self._dirs:
            for fname in os.listdir(dir):
                if fname.startswith('note_') and fname.endswith('.txt') and fname.count('.')==2:
                    filename = os.path.join(dir, fname)
                    names.add(os.path.splitext(filename)[0])  # name is filename minus .txt
        return names
    
    def get_note(self, name):
        return FileNote(name + '.txt')
    
    def new_note(self):
        tstamp = datetime.datetime.now().strftime(FileNote._FILENAME_FORMAT)
        filename = os.path.join(self._dirs[0], '%s.1.txt' % tstamp)
        with open(filename, 'wb') as f:
            pass



class BaseNote:
    def id(self):
        return self.name().split('.')[0]
    
    def seq(self):
        return int(self.name().split('.')[1])
    
    def name(self):
        raise NotImplementedError()
    
    def datetime(self):
        raise NotImplementedError()
    
    def text(self):
        raise NotImplementedError()
    
    def setText(self, text):
        raise NotImplementedError()



class FileNote(BaseNote):
    _FILENAME_FORMAT = 'note_%Y%m%d_%H%M%S'
    
    def __init__(self, filename):
        self._filename = filename
        self._parse_name()
        
        # Init text, is lazily loaded
        self._text = None
        
        # Parse datetime
        try:
            self._dt = datetime.datetime.strptime(os.path.basename(self.id()), self._FILENAME_FORMAT)
        except ValueError:
            self._dt = datetime.datetime.now()
    
    def _parse_name(self):
        self._name = os.path.splitext(self._filename)[0]
        self._id = self.name().split('.')[0]
    
    def name(self):
        return self._name
    
    def id(self):
        return self._id
    
    def datetime(self):
        return self._dt
    
    def text(self):
        if self._text is None:
            # todo: check exist and prevent reading too large (binary) files
            with open(self._filename, 'rb') as f:
                self._text = f.read().decode('utf-8', 'ignore')  
        return self._text
    
    def setText(self, text):
        if text == self._text:
            return
        
        # Store new text
        self._text = text
        
        # First remove old file
        try:
            os.remove(self._filename)
        except Exception:
            pass
        
        # Update filename, name and id
        self._filename = '%s.%i.txt' % (self.id(), self.seq()+1)
        self._parse_name()
        
        # Save
        with open(self._filename, 'wb') as f:
            f.write(text.encode('utf-8'))

