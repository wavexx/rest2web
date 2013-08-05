#!/usr/bin/python
# r2w.py

# Subversion Details
# $LastChangedDate: 2005-10-17 09:18:47 +0100 (Mon, 17 Oct 2005) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web.py $
# $LastChangedRevision: 139 $

# A website creation tool using docutils (reST markup)
# http://www.voidspace.org.uk/python/rest2web

# Copyright Michael Foord, 2004 - 2006.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates, and support, please join the
# rest2web mailing list.
# https://lists.sourceforge.net/lists/listinfo/rest2web-develop
# Comments, suggestions, and bug reports, welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk


"""
A tool for autogenerating websites, or parts of websites.

Uses ReST markup - http://docutils.sourceforge.net/rst.html
Uses the template system from Firedrop - http://zephyrfalcon.org/labs

The basic idea is that it starts in the 'start_directory' and scans for files
to build. It compares them to the existing files in the 'compare_directory'.
If they are different it saves the new files in the 'target_directory'.

This works only if you keep a full copy of your website on your local
filesystem, but allows you to just save out only the files that have changed.

To work out what files to build we are looking for directories with text files
in. We scan the directory and then all subdirectories (one layer down) in
order to build the index.

We will only know to build a directory if there is an index.txt .
This must either be a page of content - or just a restindex.

For generating the breadcrumbs navigation, we assume that the start_directory
is the top level. 
"""

import os
import sys
import time
import imp
from StringIO import StringIO
from traceback import print_exc

# add the pythonutils directory to the path
# in case it's not properly installed
if os.path.isdir('pythonutils'):
    sys.path.append(os.path.abspath('pythonutils'))

from rest2web.pythonutils.standout import StandOut
from rest2web.pythonutils.configobj import ConfigObj
from rest2web.pythonutils.cgiutils import istrue

import rest2web
from rest2web import __version__
from rest2web.restprocessor import Processor
from rest2web.command_line import handle_args
from rest2web.printing import WARN, ACTION, INFO, OVERRIDE, THRESHOLD, out
from rest2web.restutils import decode

from rest2web import printing

# set locale for guessing encoding
import locale
locale.setlocale(locale.LC_ALL, '')

versionstring = 'rest2web version %s' % __version__

# edit this to change default behaviour
cfg_file = 'r2w.ini'
old_cfg_file = 'rest2web.ini'

force_mode_config = {
    'start_directory': '.',
    'target_directory': 'html',
    'compare_directory': '',
    'macros': '',
    'log_file': '',
    'skip_html': 'True',
}

def main(options, config):
    """
    Process all the files in the start_directory and below.
    Return the number of files processed.
    """
    #
    # create a processor
    processor = Processor(options, config)
    #
    # Now we do the business :-)
    return processor.walk()
    # NOTE: returning the count here contravenes
    # NOTE: GvR advice about ``main`` functions


def get_config():
    options = handle_args()
    cfg = options.get('cfg_file', cfg_file)
    # load the config file
    if not os.path.isfile(cfg) and not os.path.isfile(old_cfg_file):
        if not options['force']:
            # FIXME: Should this output to stderr ?
            print 'IOError: Config File Couldn\'t be Found.'
            print 'Couldn\'t find "%s".' % cfg
            sys.exit(1)
        config = ConfigObj(force_mode_config)
        
    else:
        if not os.path.isfile(cfg):
            print >> sys.stderr, 'Use of "rest2web.ini" is deprecated. Please rename it to "r2w.ini" instead.'
            cfg = cfg_file
        config = ConfigObj(cfg)
    #
    return options, config

############################################################

if __name__ == '__main__':
    options, config = get_config()
    if os.path.isfile('__dist__'):
        print 'Won\'t run from distribution directory.'
        print "Run 'make_dist.py' and use the distribution it creates."
        sys.exit(1)
    #
    config['defaults_directory'] = os.path.join(
        os.path.dirname(rest2web.__file__), 'defaults')
    #
    #FIXME: check this returns an integer
    threshold = THRESHOLD[options.get('verbosity', 0)]
    log_file = config['log_file'] or None
    if log_file:
        log_file = os.path.expanduser(log_file)
    #
    # create the 'logger'
    stand = StandOut(logfile=log_file)
    # Log *everything* to the file.
    stand.errThreshold = 1
    stand.outLogfileThreshold = 1
    # Set the normal output level, as per the command line option
    stand.outStreamThreshold = threshold
    #
    if istrue(config.get('psyco', 'False')):
        try:
            import psyco
            psyco.full()
            from psyco.classes import *
        except ImportError:
            out('Cannot find Psyco, skipping it', INFO)
    #
    out(versionstring, INFO)
    out('Running rest2web the Site Builder.', INFO)
    # for the logfile
    out(time.ctime() + '\n', INFO)
    #
    time1 = time.time()
    try:
        # do the business
        count = main(options, config)
    except KeyboardInterrupt:
        sys.stderr.write('Exited by Keyboard Interrupt.\n')
    except Exception, e:
        # print any error without bombing out
        # (so we can display it, then close our files nicely)
        f = StringIO()
        print_exc(file=f)
        # write error to sys.stderr rather than printing to sys.stdout
        sys.stderr.write(f.getvalue() + '\n')
    else:
        out(('\nTime taken to build site was %.3f seconds.' %
            (time.time() - time1)), INFO)
        out('%s files processed.' % count, INFO)
    #
    stand.close()
    #
    if (not options.get('nopause', False) 
           and istrue(config.get('pause', 'False'))):
        raw_input('Hit return to continue >>> ')
    sys.exit(printing.ERROR_STATUS)


"""
CHANGELOG
=========

2006/08/21
----------

Updated to new version of StandOut and removed unused py2exe support.
(Further work needed!)

2006/08/13
----------

Default start message changed from 'OVERRIDE' level, to 'INFO'.

Changes so that the config file can be omitted in 'force mode'.

2006/08/06
----------

Added support for command line 'nopause'.

2006/08/03
----------

Fixed bug with ``standerr`` where no logfile is used.


2006/07/29
----------

All pythonutils modules now imported from 'rest2web.pythonutils'.


2006/04/17
----------

Further code cleanup.

Command line options are now passed to the Processor.

Removed support for ConfigObj 3.

Won't run in the distribution directory - need to run "make_dist.py".


2006/04/05
----------

Added verbosity levels.

Added support for uservalues in the config file.

2006/04/03
----------

Added support for command line options in general, and verbosity in particular.

Set the log file to log *everything*.

2006/01/27
----------

A sensible error message is displayed if the config file is missing.

2005/10/13
----------

Added support for debug.

2005/08/29
----------

Added psyco and pause config options

We now need cgiutils from pythonutils as well

Changed pythonutils imports

We trap ``KeyboardInterrupt``

Now depends on pythonutils 0.2.0


2005/08/05
----------

Added support for ConfigObj 4 *and* 3.

Pass config to the processor.


2005/06/22
----------

Refactoring to simplify.

Moved a lot into restprocessor.py

2005/06/20
----------

Added 'pythonutils' directory to sys.path
    (moved pythonutils to svn)

2005/06/17
Updated version in __init__.py
Changes by Nicola Larosa
    Added warning if psyco not found
    Code cleanup
        lines shortened
        comments on line above code
        empty comments in empty lines

2005/05/30
----------

Added macrodir to the Processor
We add the modules directory to sys.path (for the macros)

2005/05/28
----------

Added fix to avoid going into subversion ('.svn') directories.

2005/05/27
----------

Added support for macros.

2005/05/08
----------

Version 0.1.0
First release.
"""

