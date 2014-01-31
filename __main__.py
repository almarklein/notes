""" Launcher for the notes.txt application.
"""

import sys
import os
from pyzolib.qt import QtCore, QtGui

# Add notes package to sys.path
THISDIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(THISDIR))

# Now we can import it
import notes

# Launch!
app = QtGui.QApplication([])
w = notes.Notes(None)
w.show()
app.exec_()
