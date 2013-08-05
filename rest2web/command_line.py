# command_line.py

# Subversion Details
# $LastChangedDate: 2006-02-18 23:57:27 +0000 (Sat, 18 Feb 2006) $
# $LastChangedBy: aji $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web/restprocessor.py $
# $LastChangedRevision: 158 $

# Handle command line options for rest2web
# http://www.voidspace.org.uk/python/rest2web/


# Copyright Michael Foord, 2004 - 2006.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates and support, please join the
# rest2web mailing list.
# http://lists.sourceforge.net/lists/listinfo/rest2web-develop
# Comments, suggestions and bug reports welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk

"""
A module that handles the command line arguments for rest2web.

For Python 2.2 it only retrieves the first argument as the config file.

For Python 2.3 and above it handles various options.

Run ``r2w.py --help`` for a list of the options.

"""

import os
import sys
from rest2web import __version__

try:
    from optparse import OptionParser
except ImportError:
    OptionParser = None

__all__ = ('handle_args',)

DEFAULTS = {
    # cfg_file not here, default supplied in r2w.py
    'verbosity': 0,
    'template': None,
    'uservalues': [],
    'force': False,
    'nopause': False,
    'skiperrors': False,
}

usage = "%prog [options] config_file"

def handle_args():
    """Handle the command line options for rest2web."""
    if not OptionParser:
        # Python 2.2
        options = dict(DEFAULTS)
        if len(sys.argv) > 1:
            options['cfg_file'] = sys.argv[1]
        return options
    return handle_optparse()

def handle_optparse():
    """Handle arguments using optparse."""
    parser = OptionParser(usage=usage,
        version="restweb %s" % __version__)
    #
    # Verbosity options
    parser.add_option('-v', dest='verbosity', help='Verbose output (default).',
        action="store_const", const=0)
    parser.add_option('-a', dest='verbosity', help='Display warnings & '
        'actions only.', action="store_const", const=1)
    parser.add_option('-w', dest='verbosity', help='Display warnings only.',
        action="store_const", const=2)
    #
    # Template File
    parser.add_option('-t', '--template-file', dest='template',
        help='Specify a template file. (Overrides first template.)')
    #
    # Uservalues
    parser.add_option('-u', '--uservalues', dest='uservalues', action='append',
        help='Global uservalues for the site, in the form "name=value".')
    #
    # Force
    parser.add_option("-f", '--force', action="store_true", dest="force",
        help="Force site without indexes, restindexes or template.")
    #
    # No pause
    parser.add_option("-n", '--nopause', action="store_true", dest="nopause",
        help="Do not pause after processing (overrides setting in config file).")
    #
    # Skip errors
    parser.add_option("-s", '--skiperrors', action="store_true", dest="skiperrors",
        help="Skip errors (continue processing).")
    #
    parser.set_defaults(**DEFAULTS)
    #
    (option_obj, args) = parser.parse_args()
    #
    # Build the options dictionary
    options = {}
    options['verbosity'] = option_obj.verbosity
    if option_obj.template:
        options['template'] = os.path.abspath(option_obj.template)
    else:
        options['template'] = None
    #
    enc = 'ascii'
    if option_obj.uservalues:
        if hasattr(sys.stdin, 'encoding') and sys.stdin.encoding:
            enc = sys.stdin.encoding
    #
    options['uservalues'] = get_uservalues(option_obj.uservalues, enc)
    options['force'] = option_obj.force
    options['nopause'] = option_obj.nopause
    options['skiperrors'] = option_obj.skiperrors
    #
    # Sort the arguments
    if args:
        if len(args) > 1:
            # This quits if the wrong number of args are passed.
            parser.error("Incorrect number of arguments.")
        options['cfg_file'] = args[0]
    return options

def get_uservalues(vals, enc):
    """Retrieve and decode the uservalues."""
    out = {}
    for v in vals:
        try:
            k, e = v.split('=', 1)
        except ValueError:
            # uservalue in incorrect format
            print 'Uservalue "%s" is incorrect format.' % v
            print 'Must be "name=value".'
            sys.exit(1)
        try:
            out[k] = unicode(e, enc)
        except UnicodeDecodeError:
            print 'Failed to decode uservalues to unicode.'
            print 'Using encoding "%s".' % enc
            sys.exit(1)
    return out

if __name__ == '__main__':
    # test code
    sys.argv = [__file__, '-v', 'pot']
    print handle_optparse()
    #
    sys.argv = [__file__, '-a', 'fish']
    print handle_optparse()
    #
    sys.argv = [__file__, '-w', 'kettle']
    print handle_optparse()
    #
    sys.argv = [__file__, '--help']
    print handle_optparse()
    #
    # Should fail !
    sys.argv = [__file__, '-w', 'fish', 'kettle']
    print handle_optparse()

"""
TODO
====

CHANGELOG
=========

2006/08/06
----------

Added support for command line 'nopause'.

2006/04/17
----------

Implemented.

"""
