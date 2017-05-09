# -*- coding: utf-8 -*-
# Copyright (C) 2013, Almar Klein
# BSD licensed.

""" 
Application for the Notes.txt note taking format.
Read more in the readme or at bitbucket.org/almarklein/notes
"""

# Information for Pyzo, when used as a tool
tool_name = "Notes"
tool_summary = "Simple but powerful note taking app."


"""
A note has:
    name: id.seq
    id: uniquely identifies that note
    seq: sequence number for that note
    text: content

"""

# todo: overview of total+shown notes, number of tasks
# todo: creating new note is buggy
# todo: deleting a note is buggy

from .app import Notes, config
