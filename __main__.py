#!/usr/bin/env python3
""" Launcher for the notes.txt application.
"""

import sys
import os
from qtpy import QtWidgets

# Add notes package to sys.path
THISDIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(THISDIR))

# Now we can import it
import notes

# Launch!
app = QtWidgets.QApplication([])
w = notes.Notes(None)
w.show()
app.exec_()
