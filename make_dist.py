# make_dist.py

# Subversion Details
# $LastChangedDate: 2005-06-24 16:01:45 +0100 (Fri, 24 Jun 2005) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web.py $
# $LastChangedRevision: 39 $

# Distribution building tool for rest2web
# http://www.voidspace.org.uk/python/rest2web/

# Copyright Michael Foord, 2004 & 2005.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates, and support, please join the
# Pythonutils mailing list.
# http://groups.google.com/group/pythonutils/
# Comments, suggestions, and bug reports, welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk

import os
import sys
import shutil
import stat
import time
from StringIO import StringIO
from traceback import print_exc
    
from rest2web.pythonutils.standout import StandOut
from rest2web.pythonutils.pathutils import walkdirs, walkfiles, walkemptydirs, onerror
from os.path import split, splitext

"""
This script makes a new distribution folder from the Working Copy.
It removes all the 'svn' stuff from the distribution.
It also removes 'pyc' files.
It also removes any generated docs/thumbnails/etc that aren't needed in the 
final distribution.

This script is also useful for creating a 'clean distribution' for running the
tests on.
"""

# directory to start in (current directory here)
source = '.'
# location to put the built distribution
dest = 'rest2web-dist'
# file extensions to delete
bad_ext = ['.html', '.pyc', '.bak']
# filenames to delete
bad_files = ['thumbs.db', 'log.txt',
            'gallery1.ini', 'gallery2.ini',
            'gallery3.ini', 'make_dist.py', '__dist__']
# whole directories to remove
bad_dirs = ['thumbnails', '.svn']
# exceptions to the 'bad_ext' rules
good_files = ['entry.html', 'page.html','gallery.html']

# path to log the process to
log_file = 'log.txt'

# pause for input after completion ?
pause = True
if sys.argv[1:] and sys.argv[1] == 'nopause':
    pause = False


def copytree(src, dst):
    """
    Modified version of copytree from shutil.

    DOesn't copy the files we don't want.
    """
    names = os.listdir(src)
    os.mkdir(dst)
    errors = []
    for name in names:
        if (name in bad_dirs) or (name in bad_files):
            continue
        ext = splitext(name)[1]
        if (ext in bad_ext) and not (name in good_files):
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.isdir(srcname):
                copytree(srcname, dstname)
            else:
                shutil.copy2(srcname, dstname)
        except (IOError, os.error), why:
            errors.append((srcname, dstname, why))
    if errors:
        raise Error, errors

def main():
    # delete the distribution directory if it exists
    if os.path.isdir(dest):
        print 'Deleting the current target directory.'
        shutil.rmtree(dest, onerror=onerror)
    #
    # copy the current copy to dest
    print 'Copying the working directory.'
    copytree(source, dest)
    #
    # remove empty directories
    # (mainly from the docs_html folder)
    print 'Trimming empty directories.'
    thelist = []
    while True:
        lastlist = thelist
        thelist = list(walkemptydirs(dest))
        if not thelist or lastlist == thelist:
            break
        for aDir in thelist:
            print 'Trimming "%s".' % aDir
            os.rmdir(aDir)
    #
    print '\nDone.'

if __name__ == '__main__':
    stand = None
    if log_file:
        stand = StandOut(logfile=log_file)
    time1 = time.time()
    try:
        # do the business
        main()
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
        print
        print ('Time taken to make distribution was %.3f seconds.' %
            (time.time() - time1))
    #
    if stand:
        stand.close()
    #
    if pause:
        raw_input('Hit return to continue >>> ')

"""
TODO
=====

* Auto-create zip and tarball
* Build executable
* MD5 hash
* replace with a monolithic setup.py ?
* What about accepting command line arguments or reading a config file for the
 details ?

Move onerror into pathutils.

ISSUES
======

None yet.

CHANGELOG
=========

2006/07/27
----------

Distribution directory is now 'rest2web-dist'.

2005/11/12
----------

``make_dist`` will now work from SVN without pythonutils installed.

Added logging of build process.

2005/11/11
----------

``onerror`` handler for ``rmtree`` - can delete read only directories.

2005/08/08
----------

Implemented to cope with the gallery files.

2005/08/01
----------

Moved into SVN

Amended for new location and for gallery files.

"""

