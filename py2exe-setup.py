# py2exe-setup.py

# Subversion Details
# $LastChangedDate: 2005-06-24 16:01:45 +0100 (Fri, 24 Jun 2005) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web.py $
# $LastChangedRevision: 39 $

# py2exe-setup.py for rest2web - for py2exe *only*
# http://www.voidspace.org.uk/python/rest2web

# Copyright Michael Foord, 2004 & 2005.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates, and support, please join the
# Pythonutils mailing list.
# http://groups.google.com/group/pythonutils/
# Comments, suggestions, and bug reports, welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk

import py2exe
import sys
import shutil
import os
from distutils.core import setup
from pathutils import walkdirs

TARGET = '../../rest2web-exe'
if os.path.isdir(TARGET):
    shutil.rmtree(TARGET)

extra_files = ['macros.py',
    'r2w.ini',
    'BSD-LICENSE.txt',
    ]

extra_dirs = ['docs', 'docs_html']

sys.argv[1:] = []
sys.argv.append('py2exe')
sys.argv.append('-d')
sys.argv.append(TARGET)

from rest2web import __version__

options = {"py2exe": {"compressed": 1,
                      "optimize": 2,
                      "packages": ['docutils', 'encodings'],
                      }}

setup(
    console =[{
                'script': 'rest2web.py',
                # anyone do a better icon ?
                'icon_resources': [(1, 'globepage.ico')],
            }],
    zipfile = "lib/shared.zip",
    version =  __version__,
    description =  'For building websites with docutils.',
    name =         'rest2web',
    author =       'Michael Foord',
    author_email = 'fuzzyman@voidspace.org.uk',
    url =          'http://sourceforge.net/projects/rest2web',
    options= options,
      )

shutil.rmtree('build')
for entry in extra_files:
    shutil.copy(entry, TARGET)
for entry in extra_dirs:
    shutil.copytree(entry, os.path.join(TARGET, entry))

svn_list = []
for aDir in walkdirs(TARGET):
    if aDir.endswith('.svn'):
        svn_list.append(aDir)
# don't delete the directories until we've walked the tree
for entry in svn_list:
    shutil.rmtree(entry)

"""
TODO
====

Make rest2web installable - create a generic setup.py

Document the macros/template restrictions when using the executable
(can only import available modules)

Make the target directory configurable
Sort the plugins system (test the gallery)

Better Icon

Single file option ?


Needed files - 
    macros.py
    r2w.ini
    BSD-LICENSE.txt
    docs directory
    docs_html directory
        (minus the '.svn' directories)

*Extra files* -
    gallery_test
    *new* .bat files needed (.exe not .py)
    the plugins directory into lib

CHANGELOG
=========

2006/08/03
Changed rest2web.ini to r2w.ini

2005/08/08
Included the modules used by macros
It copies files needed by the distribution and cleans up after itself

2005/08/01
Moved into SVN

"""


# need to set a directory and force the encodings
