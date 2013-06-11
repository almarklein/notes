# NOTES.txt
  
This is a specification of a simple, text-only protocol for storing and
selecting notes. The protocol explicitly differentiates between notmal
notes (i.e. journal entries), tasks, and ideas (as in a [spark
file](https://medium.com/the-writers-room/8d6e7df7ae58)). It also makes
use of hashtags (which are #great) to organize notes.

This repo also contains an app that implements the protocol. It is
written as a tool for the IEP IDE, but with a bit of refactoring it can
be a standalone app too.


# Introduction
  
The idea is to maintain a (large) collection of text notes, and allow
the user to very easily select all notes accoring to simple critera.

There are three kind of notes: tasks, ideas and normal notes. All these
notes are stored in one heap and shown chronologically by default.


# Note storage
  
Multiple notes can be stored in a text file. Notes are separated by
lines that start with ``----``. Optionally, this separater line also
contains a date (and time). The date should be formatted as:
``YYYY-MM-DD``. Time (if given) should be formatted as ``HH:MM`` or
``HH:MM:SS``.

TODO: Allow other date formats?

This simple note format makes it easy for other applications to hook
into the notes system, and the user can easily manage his/her notes
using a simple text editor.


# Specifying note type
  
Each note can start with a prefix to identify its type:

:::plain
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

    This is a note about #tags 
    For instance #home, or #work, or #myproject 
    To help retrieving notes, users are encouraged to 
    specify at least one tag per note.
    

# Selection syntax
  
This format also specifies a simple syntax for selecting notes. An
application supporting this format will typically have a one-line
text-box into which you can write your query. This sounds a bit
old-school or comman-line style, but bear with me; the syntax is really
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
    

# Syncing and scaling up to large amounts of notes
  
Just place the notes file in your dropbox folder to sync it between
devices and back it up automatically. Dropbox also provides a history
of your file.

Applications that implement this protocol can (and are encouraged to)
support reading from multiple files simultaneously. This can help
prevent synchronisation conflicts, and can help keep the note files
relatively small.

For instance, use a "notes.txt", and a "notes_phone.txt". Both files
can then be updated independently (also off-line) without fear of
syncing problems.

If your "note.txt" grows too large, rename it notes_old.txt, and create
a new "notes.txt". The application will still allow to transparently
see and edit all notes, but the old one will probably not be updated
as often.

The application should be able to cope with large amount of notes
(possibly coming from different files. This means that a lightweight
minimal representation of each note should maintained, but that widgets
are only created for notes that are shown. Possibly, extra widges are
created on the fly as the user scrolls through the notes.
