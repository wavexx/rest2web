# printing.py

# Subversion Details
# $LastChangedDate: 2006-01-05 12:06:07 +0000 (Thu, 05 Jan 2006) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web/printing.py $
# $LastChangedRevision: 155 $

# Helper functions for rest2web
# Primarily functions that handle the docutils/encodings stuff
# http://www.voidspace.org.uk/python/rest2web/

# Copyright Michael Foord, 2004 - 2006.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates and support, please join the
# rest2web mailing list.
# https://lists.sourceforge.net/lists/listinfo/rest2web-develop
# Comments, suggestions and bug reports welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk

"""
This module provides two print functions.

If StandOut is in use, then ``standout`` should be used, otherwise ``standard``
should be used.

If you use ``standout`` you can pass in a verbosity level for the current
message. (This parameter will be ignored by the ``standard`` function.)

It also defines four constants for message priority levels :

    OVERRIDE
    WARN
    ACTION
    INFO
    
The VERBOSITY dictionary maps different verbosity levels (integers) to the
right setting to pass to StandOut.
"""

import sys

__all__ = (
    'WARN',
    'ACTION',
    'INFO',
    'OVERRIDE',
    'standard',
    'standout',
    'VERBOSITY',
)

OVERRIDE = 9
WARN = 7
ACTION = 3
INFO = 1

# maps verbosity level to the right setting
THRESHOLD = {
    # verbose (default)
    0: 1,
    # Actions & Warnings
    1: 3,
    # Warnings Only
    2: 7,
}

def out(line, level=INFO, newline=True):
    """Print a line if StandOut is enabled."""
    global ERROR_STATUS
    if level == WARN:
        ERROR_STATUS += 1
        stream = sys.stderr
    else:
        stream = sys.stdout
    stream.write(line, level)
    if newline:
        stream.write('\n', level)
    else:
        stream.write(' ', level)

ERROR_STATUS = 0


"""
TODO
====

Find a way of using this from within plugins.

CHANGELOG
=========

2006/08/21
----------

Changed VERBOSITY to THRESHOLD.

Changed standout to out.

This is support for standout version 3.


2006/04/05
----------

First implementation.

"""