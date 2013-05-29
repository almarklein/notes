# NOTES

This is a simple, text-only note taking app and task manager.
It is written as a tool for the IEP IDE, but perhaps it can be a standalone app too.

I probably need a different name. Perhaps "tanoid" (TAsks-NOtes-Ideas)?


## Introduction

The idea is maintain a collection of text notes, and allow the user to
very easily select all notes accoring to certain critera.

There are three kind of notes: tasks, ideas and normal notes. The latter may
for instance be journal entries. All these notes are stored on one heap and
shown chronologically by default.

So basically, this app, is a task manager, a spark file, a journal and a note
taking app, all in one.



## Note syntax

This section defines the note syntax. Different applications could use the same syntax.

### Note storage

Multiple notes can be stored in a text file. Notes are separated by lines that start with ``----``.
Optionally, this separater line also contains a date (and time). The date should be 
formatted as: ``YYYY-MM-DD``. Time (if given) should be formatted as ``HH:MM`` or ``HH:MM:SS``.

Allow other date formats?

This simple note format makes it easy for other applications to hook into the notes system,
and the user can easily manage his/her notes using a simple text editor. 


### Note type

  * Tasks start with ``!``, ``!!`` or ``!!!`` (more is higher priority)
  * Ideas start with ``?``
  * Any other note is a normal note
  * Completed task start with ``x`` followed by the exclamation marks
  
Perhaps ...

  * Use only two levels of priority?
  * Allow using multiple levels for tags and ideas too (sticky notes and 'good' ideas)
  * Normal notes (journal entries?) can start with ``%``
  * Completed task start with a dot ``.`` (similar to hidden files on Linux), and notes can also be hidden.


### Tags

Each note can have zero or more tags. You create a tag simply by starting a word with ``#``, similar
to hashtags in twitter of G+. Tags define a context and allows the user to easily (and quickly) select
certain notes of interest.

Users are encourages to at least specify one tag per note.


## Application

This section describes the application that I'm developing. It should be possible to develop other 
applications on the syntax definitions defined above.


### Selecting

A simple line-edit allows the user to type a select-query. These should be very simple and the
list ceacts instantly. One or more dropdown menus inside the line-edit provide all the available
commands and tags.

The user can type ``!`` or ``?`` to select only tasks or ideas, respectively. The user
can type type tags to select only notes with these tags. 

Furter, the user can type normal words, in which case a search is performed (may be slower) for 
notes containing these words.

All queries are case insensitive.


### Sorting

It should feel a bit like having a big file, so the latest / most important notes are 
at the bottom. By default (all notes are selected) the application sorts the
notes in chronological order. Notes with no date (or an invalid date) are ... I don't know yet/

If a certain note type is selected (i.e. tasks or ideas) the notes are first sorted 
by priority, and then by time. 

Perhaps ...

  * The user can reverse the sorting order
  * The user can select messages based on their date


### Dealing with large amount of notes

The application should be able to cope with large amount of notes. This means that a 
lightweight minimal representation of each note is maintained, but that widges are only
created for notes that are shown. Extra widges are created on the fly as the user scrolls 
through the notes.

The application can use multiple note-files simultaneously so that notes can be divided
over them. Among other things, this keeps the individual files relatively small.

### Syncing

Use dropbox. But better keep a separate file for each "source" to prevent sync conflicts.




