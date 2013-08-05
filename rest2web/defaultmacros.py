# defaultmacros.py

# Subversion Details
# $LastChangedDate: 2006-08-05 18:22:35 +0100 (Sat, 05 Aug 2006) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/macros.py $
# $LastChangedRevision: 192 $

# macros for rest2web 
# http://www.voidspace.org.uk/python/rest2web

# Adapted from macros.py for Firedrop2 by Hans Nowak
# http://zephyrfalcon.org

# Copyright Michael Foord & Hans Nowak, 2004 - 2006.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates and support, please join the
# rest2web mailing list.
# http://lists.sourceforge.net/lists/listinfo/rest2web-develop
# Comments, suggestions and bug reports welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk



import cStringIO
import os
import sys
import traceback
import rest2web.modules.smiley as smiley_module
import rest2web.modules.colorize as color


# curlyl and curlyr is a way of including literal
# curly brackets in pages
curlyl = '{'
curlyr = '}'

cl = curlyl
cr = curlyr

lt = '&lt;'

smiley_directory  = None
smiley_url = '<% path_to_root %>images/smilies/'
emoticon_url = '<% path_to_root %>images/'

# {emoticon;name}  e.g. {emoticon;smile}
def emoticon(name):
    """
    Return a link to a named gif file
    in the <% path_to_root %>images/ folder.
    """
    name = name.strip()
    return ('<img src="%s%s.gif" alt="emoticon:%s" />' %
        (emoticon_url, name, name))

emo = emoticon

def escape(inval):
    """
    Escape a string as a single template value.
    
    Same effect as the ``:raw:role``.
    """
    return '<%% %s %%>' % inval
esc = escape

def acronym(acronym, meaning=None):
    """
    Return the HTML for an acronym.
    """
    if meaning is None:
        # will raise a KeyError if the acronym isn't found
        meaning = default_acronyms[acronym.lower()] 
    return '<acronym title="%s">%s</acronym>' % (meaning, acronym)

acro = acronym

# a dictionary of standard acronyms
# keys should be lowercase
default_acronyms = {
    'wysiwyg': 'What You See Is What You Get',
    'html': 'HyperText Markup Language',
    'xml': 'eXtensible Markup Language',
    'xhtml': 'eXtensible HyperText Markup Language',
    'rest': 'ReStructuredText',
    'css': 'Cascading Style Sheets',
    'ie': 'Internet Exploder',
    'afaik': 'As Far as I Know',
    'ianal': 'I am not a Lawyer',
    'ssi': 'Server Side Includes',
    'cgi': 'Common Gateway Interface',
    'lol': 'Laughing Out Loud',
    'rotfl': 'Roll On the Floor Laughing',
    'http': 'HyperText Transfer Protocol',
    'ascii': 'American Standard Code for Information Interchange',
    'gui': 'Graphical User Interface',
    'cli': 'Command Line Interface',
    'pda': 'Personal Digital Assistant',
    'rtfm': 'Read the Manual',
    'ftp': 'File Transfer Protocol',
    'nntp': 'Network News Transfer Protocol',
    'uk': 'United Kingdom',
    'pc': 'Personal Computer',
    'url': 'Uniform Resource Locator',
    'uri': 'Uniform Resource Identifier',
    'tcp/ip': 'Transport Control Protocol/Internet Protocol',
    'udp': 'User Data Paragram',
    }


def include(filename, escape='False'):
    """
    Include a file in the page.
    HTML only of course.
    """
    data = open(os.path.expanduser(filename), 'r').read()
    # should we check for invalid (misspelt) options and raise an error ?
    if escape.lower() not in ['false', 'off', '0', 'no']:
        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')
        data = data.replace('\n', '<br />\n').replace('  ', '&nbsp;&nbsp;')
    return data

inc = include


smile = None
def smiley(text):
    """
    Create a smiley.
    The smiley lib is only created on the first run through.
    """
    global smile
    if smile is None:
        smile = smiley_module.lib(
                                smiley_directory,
                                smiley_url)
    return smile.makehappy(' %s ' % text).replace('\n', '')

sm = smiley


#
# syntax coloring
def colorize(filename):
    """
    format a python script as html
    
    Using the appropriate css it will be nicely colored.
    Needs the colorize.py module.
    """
##    fullname = os.path.join(filename)
    f = open(os.path.expanduser(filename), 'r')
    data = f.read()
    f.close()
    #
    p = color.Parser(data)
    p.format(None, None)
    src = p.getvalue()
    return src.replace('\n', '<br />\n').replace('  ', '&nbsp;&nbsp;')
    # to avoid having to use <pre>..

col = colorize

class coloring:

    def open(self, data):
        p = color.Parser(data)
        p.format(None, None)
        src = p.getvalue()
        return src.replace('\n', '<br />\n').replace('  ', '&nbsp;&nbsp;')

    def close(self, *args):
        pass


def name(n):
    return '<a name="%s" id="%s"></a>' % (n, n)

def title(text, size=3):
    """For titles of a named size"""
    return '<h%s>%s</h%s>' % (size, text, size)

def small(text):
    return '<small>%s</small>' % text


"""
TODO

CHANGELOG

2006/08/13
Changes to make this the 'defaultmacros.py'

2006/04/14
Added escape.
Added namespace and uservalues.

2005/10/16
Added name, title, small
Added several acronyms to the standard dictionary.


2005/06/18
Changes by Nicola Larosa
    Code cleanup
        lines shortened
        comments on line above code
        empty comments in empty lines

2005/06/16
Added a set of standard acronyms.

2005/06/05
Replace extraneous '\n' in the output of the smile macro. 

2005/06/03
Added the coloring advanced macro.

2005/05/31
curlyl and curlyr added.
Some docstrings added.
Removed __all__ as it's not actually used.
Changed the smiley macro so that it doesn't create a new smiley object
each run through.
colorize raises an import error if you attempt to use it and colorize.py
isn't available.
Added escape option to the include macro.
In the event of error - colorize raises the error rather than trapping it.
Added the col=colorize alias.
Added the inc=include alias.

2005/05/28
Integrated with rest2web, via the config file.
"""

