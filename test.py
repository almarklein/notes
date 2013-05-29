
import datetime
import random
import os
import sys

testdir = '/home/almar/notes_test'

_FILENAME_FORMAT = 'note_%Y%m%d_%H%M%S'

thetime = datetime.datetime.now()
oneminute = datetime.timedelta(0,1)

##

filename = os.path.join(testdir, 'notes.txt')

with open(filename, 'wb') as f:
    
    for i in range(10):
        text = 'dorum epsilum enzo en wat dan ook lalala\n'*5 + '\n'
        title = '---- %s\n' % thetime.strftime('%Y-%m-%d %H:%M:%S')
        f.write(title.encode('utf-8'))
        f.write(text.encode('utf-8'))


##
for i in range(10000):
    thetime = thetime - oneminute
    
    text = 'dorum epsilum enzo en wat dan ook lalala'*5
    tstamp = thetime.strftime(_FILENAME_FORMAT)
    filename = os.path.join(testdir, '%s.1.txt' % tstamp)
    
    with open(filename, 'wb') as f:
        f.write(text.encode('utf-8'))


##
notes = []
for fname in os.listdir(testdir):
    filename = os.path.join(testdir, fname)
    with open(filename, 'rb') as f:
        text = f.read().decode('utf-8', 'ignore')
        notes.append(text)
