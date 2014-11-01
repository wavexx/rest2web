# restutils.py

# Subversion Details
# $LastChangedDate: 2006-05-01 15:51:03 +0200 (Mon, 01 May 2006) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web/restutils.py $
# $LastChangedRevision: 172 $

# Helper functions for rest2web
# Primarily functions that handle the docutils/encodings stuff
# http://www.voidspace.org.uk/python/rest2web

# Copyright Michael Foord, 2004 - 2006.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates and support, please join the
# rest2web mailing list.
# https://lists.sourceforge.net/lists/listinfo/rest2web-develop
# Comments, suggestions and bug reports welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk

import os
import sys
import random
import locale
import validate
from docutils import core

# do a quick test that we have a recent enough version of docutils
# 0.3.9 is the minimum required version of docutils
MINVERSION = '0.3.9'
import docutils
if ([int(val) for val in docutils.__version__.split('.') if val.isdigit()] <
        [int(val) for val in MINVERSION.split('.') if val.isdigit()]):
    print 'You have version "%s" of docutils.' % docutils.__version__
    print 'The minimum required version is "%s".' % MINVERSION
    print 'Exiting.'
    sys.exit(1)

__all__ = (
        'description_rest',
        'guess_encoding',
        'html_parts',
        'uni_dict',
        'encode',
        'enc_uni_dict',
        'gen_prefix',
        'listswap',
        'interactive',
        'comparefiles',
        'decode',
        'istrue'
        )

def gen_prefix(length = 4):
    """
    Generate a random string for prefixing ids.
    
    This can be used to make footnote references (etc) unique,
    where you have multiple fragments generated by docutils.
    """
    alphanum = 'abcdefghijklmnopqrstuvwxyz0123456789'
    outstring = []
    for num in range(length):
        # random character
        outstring.append(alphanum[int(random.random()*36)])
    return ''.join(outstring)

def description_rest(text, encoding, prefix = None):
    """
    Turns reST formatted text to HTML, with an explicit input coding specified.
    
    Transforms description chunks into html using html_parts.
    Handles making footnote names/hrefs/id's unique.
    Returns an unicode string.
    """
    if not text.startswith('\n'):
        text = '\n' + text
    if prefix is None:
        prefix = gen_prefix()
    #
    parts = html_parts(text, initial_header_level = 2, doctitle = 0,
        toc_backlinks = 0, input_encoding=encoding, id_prefix = prefix)
    return parts['fragment']

def guess_encoding(data):
    """
    Given a byte string, guess the encoding.
    
    Tries the standard 'UTF8', 'ISO-8859-1', and 'cp1252' encodings,
    Plus several gathered from locale information.
    
    The calling program *must* first call
        locale.setlocale(locale.LC_ALL, '')
    
    If successful it returns
        (decoded_unicode, successful_encoding)
    If unsuccessful it raises a ``UnicodeError``
    """
    encodings = ['ascii', 'UTF-8']
    successful_encoding = None
    try:
        encodings.append(locale.nl_langinfo(locale.CODESET))
    except AttributeError:
        pass
    try:
        encodings.append(locale.getlocale()[1])
    except (AttributeError, IndexError):
        pass
    try:
        encodings.append(locale.getdefaultlocale()[1])
    except (AttributeError, IndexError):
        pass
    # latin-1
    encodings.append('ISO8859-1')
    encodings.append('cp1252')
    for enc in encodings:
        if not enc:
            continue
        try:
            decoded = unicode(data, enc)
            successful_encoding = enc
            break
        except (UnicodeError, LookupError):
            pass
    if successful_encoding is None:
         raise UnicodeError('Unable to decode input data. Tried the'
            ' following encodings: %s.' % ', '.join([repr(enc)
                for enc in encodings if enc]))
    else:
        if successful_encoding == 'ascii':
            # our default ascii encoding
            successful_encoding = 'ISO8859-1'
        return (decoded, successful_encoding)

def html_parts(
        input_string,
        source_path = None,
        destination_path = None,
        # FIXME: default encoding is hardcoded
        input_encoding = 'unicode',
        doctitle = 1,
        initial_header_level = 1,
        **args):
    """
    Given an input string, returns a dictionary of HTML document parts.
    
    Dictionary keys are the names of parts, and values are Unicode strings;
    encoding is up to the client.
    
    Parameters:
    
    - `input_string`: A multi-line text string; required.
    - `source_path`: Path to the source file or object.  Optional, but useful
      for diagnostic output (system messages).
    - `destination_path`: Path to the file or object which will receive the
      output; optional.  Used for determining relative paths (stylesheets,
      source links, etc.).
    - `input_encoding`: The encoding of `input_string`.  If it is an encoded
      8-bit string, provide the correct encoding.  If it is a Unicode string,
      use "unicode", the default.
    - `doctitle`: Disable the promotion of a lone top-level section title to
      document title (and subsequent section title to document subtitle
      promotion); enabled by default.
    - `initial_header_level`: The initial level for header elements (e.g. 1
      for "<h1>").
    """
    overrides = {
        'input_encoding': input_encoding,
        'doctitle_xform': doctitle,
        'initial_header_level': initial_header_level,
        'halt_level': 2,
        'cloak_email_addresses': True,
        'stylesheet' : '',
        '_stylesheet_required': False,
        'embed_stylesheet': False,
    }
    # you can pass in an id_prefix here
    overrides.update(args)
    parts = core.publish_parts(
        source=input_string, source_path=source_path,
        destination_path=destination_path,
        writer_name='html', settings_overrides=overrides)
    return parts

def uni_dict(indict, encoding):
    """
    Given a dictionary keyed by encoded strings, return it all unicoded.
    
    This means that keys and values must be decoded.
    Returns a dictionary.
    
    Because of our particular needs (restprocessor.py) we special case
    the None key
    
    encoding can not be None
    """
    out_dict = {}
    for entry in indict:
        if entry is not None:
            uni_entry = unicode(entry, encoding)
        else:
            uni_entry = None
        val = unicode(indict[entry], encoding)
        out_dict[uni_entry] = val
    return out_dict

def enc_uni_dict(uni_dict, encoding):
    """Given a unicode dictionary, encode it.
    
    Given a dictionary with unicode keys and entries,
    encode the keys and entries.
    
    If encoding is None, it is left as unicode.
    
    If the key is None, the key is left as None.
    """
    if encoding is None:
        # XXXX returns a reference, should we return a copy?
        return uni_dict
    out_dict = {}
    for entry in uni_dict:
        if entry is not None:
            enc_entry = entry.encode(encoding)
        else:
            enc_entry = None
        val = uni_dict[entry].encode(encoding)
        out_dict[enc_entry] = val
    return out_dict

def encode(instring, encoding='ascii'):
    """
    The opposite of the unicode function.
    
    Given a unicode string, return an encoded string.
    Except if encoding is None, the string is returned unchanged.
    """
    if encoding is None or instring is None:
        return instring
    return instring.encode(encoding)

def decode(indict, encoding):
    """
    Recursively decode dictionary members into unicode, using the supplied
    encoding. (It doesn't decode keys.)
    
    Members may be strings, dictionaries, or lists/tuples of strings.
    """
    out = {}
    def dec(instring):
        return instring.decode(encoding)
    for key, value in indict.items():
        if isinstance(value, dict):
            out[key] = decode(value, encoding)
        elif isinstance(value, (tuple, list)):
            out[key] = map(dec, value)
        else:
            out[key] = value.decode(encoding)
    return out

def listswap(inlist, val1, val2):
    """
    Modifies a list in place.
    elements == val1 it swaps for val2
    """
    i = -1
    while i < len(inlist)-1:
        i += 1
        if inlist[i] == val1:
            inlist[i] = val2

def istrue(string):
    v = validate.Validator()
    return v.check('boolean', string)

def interactive(localvars=None):
    """Interactive interpreter for debugging."""
    if localvars == None:
        # extract locals from the calling frame - taken from IPython
        localvars = sys._getframe(0).f_back.f_locals
    from code import InteractiveConsole
    con = InteractiveConsole(localvars)
    con.interact()
    
def comparefiles(src, dst):
    """
    Compare two files for timestamp and filesize.
    
    Returns true if they are identical.
    
    The source file *must* exist.
    """
    if not os.path.isfile(dst):
        return False
    if not os.path.getmtime(src) == os.path.getmtime(dst):
        return False
    if not os.path.getsize(src) == os.path.getsize(dst):
        return False
    return True

"""
CHANGELOG
=========

2006/04/03
----------

Added ``comparefiles``.

2005/10/26
----------

Removed ``import_path`` - now in pathutils.

2005/10/16
----------

Added ``embed_stylesheet`` option for docutils '0.3.10'.

2005/10/13
----------

Removed dictObj

Added interactive (support for debug)

2005/07/23
Added dictObj

2005/06/18
Changes by Nicola Larosa
    Code cleanup
        lines shortened
        comments on line above code
        empty comments in empty lines

2005/06/05
Upped version of docutils required to 0.3.9

2005/05/31
Added listswap function.

2005/05/28
Added import_path function.

2005/05/22
We now require docutils version 0.3.8 or more recent.
We take advantage of the 'id_prefix' config setting.

2005/05/16
Set ``'halt_level' : 2`` - this means that more errors raise exceptions.
Removed ``from urlpath import *``
Added the test for minimum version of docutils.
Changed the bare ``except``s in ``guess_encoding``.
Added the ``uni_dict``, ``encode``, and ``enc_uni_dict``, functions.

2005/05/15
``description_rest`` now returns a unicode string.


ISSUES

Should the halt level be in a config file ?
Can we have a useful test here ?
"""

