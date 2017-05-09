# NOTES.txt
  
This is a specification of a simple, text-only protocol for storing and
selecting notes. The protocol explicitly differentiates between notmal
notes (i.e. journal entries), tasks, and ideas (as in a [spark
file](https://medium.com/the-writers-room/8d6e7df7ae58)). It also makes
use of hashtags (which are #great) to organize notes.

This repo also contains an app that implements the protocol. 


# Introduction
  
The idea is to maintain a (large) collection of text notes, and allow
the user to very easily select all notes accoring to simple critera.

There are three kind of notes: tasks, ideas and normal notes. All these
notes are stored in one heap and shown chronologically by default.


# Note storage
  
Multiple notes can be stored in a text file. Notes are separated by
lines that start with ``----``. This separater line can also
contain extra information, organized in key-value pairs separated by commas.
Currently supported are *id*, *c* (created) and *m* (modified).
For example: ``---- id:asjasdb32b2323g23jg23j c:2014-01-30 m:2014-01-31 11:36``

For ease of use one can also specify simply the date (and time). 
The date should be formatted as: ``YYYY-MM-DD``. Time (if given) should
be formatted as ``HH:MM`` or ``HH:MM:SS``.

This simple note format makes it easy for other applications to hook
into the notes system, and the user can easily manage his/her notes
using a simple text editor.


# Specifying note type
  
Each note can start with a prefix to identify its type:

    % This is a normal note 
    ----- 
    ! This is a task 
    ---- 
    ? This is an idea 
    ---- 
    This is also a normal note 
    The percent sign is optional.
    
Notes can be prioritized (three levels are supported):

    !! Finish this task quickly! 
    ---- 
    !!! This task is even more important 
    ---- 
    ?? This is a particularly good idea 
    ---- 
    %% This would be sort of like a sticky note 
    Prioritizing makes the most sense for tasks.
    
Finally, any note that starts with a dot is hidden. You can of course
delete notes, but sometimes it's nice to look back at all the tasks
that you've accomplished.

    .! A completed task 
    ---- 
    .? An idea that turned out to be a bad one
    ---- 
    .Some note that may be irrelevant now
    

# Using tags
  
Each note can have zero or more tags. You create a tag simply by
starting a word with ``#``, similar to hashtags in twitter of G+. Tags
define a context and allows the user to easily (and quickly) select
certain notes of interest.

    % This is a note about #tags 
    For instance #home, or #work, or #myproject 
    To help retrieving notes, users are encouraged to 
    specify at least one tag per note.
    

# Selection syntax
  
This format also specifies a simple syntax for selecting notes. An
application supporting this format will typically have a one-line
text-box into which you can write your query. This may sound a bit
old-school, but bear with me; the syntax is really
easy!

Firstly, if the query is empty, all notes of all types (except hidden
notes) are shown in chronological order. Notes with no date are
considered infinitelt old.

To select a type of note, the first word of the query should simply
match the note type:

    %  (Select all normal notes) 
    !  (Select all tasks) 
    ?  (Select all ideas) 
    .  (Select all hidden notes) 
    !!  (Select all tasks with priority 2 and higher)
    
If a particular type of note is selected, the notes are organized by
priority (and then chronologically).

The query can further contain tags. The application may provide you
with an easy way to see all used tags. The tags are case insensitive.
If multiple tags are given, the result is the AND of the subqueries:

    ! #work  (Select all tasks related to work) 
    ! #work #cloud  (Select all tasks that are related to work AND to "cloud")
    #home  (Select all notes related to home) 
    # (Select all notes that have no tags)
      
Finally, the query can also contain plain words. In this case the
applicaton will search through the full texts of all notes, and the
selection may therefore be less fast if you have many notes. It is up
to the application to support only whole words or also partial words.
All word searches are case insensitive though.

    ! #work Ian  (Select all work-related tasks that mention Ian) 
    ? cloud  (Select all ideas that have the word "cloud" in them)
    

# Advanced selection syntax
  
TODO:

  * Reversing order
  * Selecting a date range
    

# Application

The application in this repo needs Python3, qtpy and PyQt5/PySide2/PyQt4/PySide.

It can also be used as a tool for Pyzo. To do so, clone the repository in your
``~/.pyzo/tools/`` folder or equivalent.


# Syncing and scaling up to large amounts of notes
  
In Notes.text one selects a folder to store the notes. Each device that
stores notes to this folder does so in its own file. In this way,
you are guaranteed to have no synchronization conflicts.

An application that displays the notes for you should read the notes
from all files that are named ``notes.<devicename>.txt``, but only
write new or modified notes to the file that corresponds to the current
device.

In this way, you can safely create new notes or modify them from any device
even when you have no internet connection. After syncing, you will simply
get the most recently modified version of each note. And you will have
a backup of the versions created by each device.

So what happens when you create a note on one device and modify it on 
another? There will be two versions of the note, but the latter has
a modified time that is later. Applications can keep track of notes
using their id. If an id is not specified explicitly, the sha1 hash
of the text of the note (not the separator line) is used. In this way
if you add a note in plain text and omit an id, it can be modified
from another divice without 'duplication' it.

The application should be able to cope with large amount of notes
(possibly coming from different files. This means that a lightweight
minimal representation of each note should maintained, but that widgets
are only created for notes that are shown. Possibly, extra widges are
created on the fly as the user scrolls through the notes.
