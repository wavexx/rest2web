# textmacros.py

# Subversion Details
# $LastChangedDate: 2006-05-01 15:51:03 +0200 (Mon, 01 May 2006) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web/textmacros.py $
# $LastChangedRevision: 172 $

# Used in rest2web
# http://www.voidspace.org.uk/python/rest2web

# By Hans Nowak
# http://zephyrfalcon.org
# (amended by Michael Foord)

# TODO: Allow {-} as closing macro.  This is less clear but more concise.

# Copyright Michael Foord & Hans Nowak, 2004 - 2006.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates and support, please join the
# rest2web mailing list.
# http://lists.sourceforge.net/lists/listinfo/rest2web-develop
# Comments, suggestions and bug reports welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk


import re

__version__ = "1.0"

class MacroError(Exception): pass
class UnbalancedMacroError(MacroError): pass

re_macro = re.compile("(\{[+-]?\w+.*?})")

class BaseMacro:
    
    def open(self, *args):
        pass
    
    def close(self, *args):
        pass

class TextMacros:

    def __init__(self, namespace = None):
        if namespace is None:
            namespace = {}
        self.namespace = namespace

    def find_macros(self, text):
        """
        Find macros in text.  Return a list of tuples (start, stop, text).
        """
        matches = []
        for m in re_macro.finditer(text):
            t = (m.start(), m.end(), m.groups()[0])
            #
            # if the macro is not in the namespace, we ignore it
            macroname = t[2][1:-1].split(';')[0]
            if macroname.startswith("+") or macroname.startswith("-"):
                macroname = macroname[1:]
            if self.namespace.has_key(macroname):
                matches.append(t)
        #
        return matches

    def split_text(self, text, matchlist):
        """
        Split text in chunks, based on list of macros returned by 
        find_macros.  Return a list of tuples (type, text) where type can
        be 'text' or 'macro'.
        """
        parts = []
        index = 0
        for (begin, end, macro) in matchlist:
            if begin > index:
                chunk = text[index:begin]
                parts.append(("text", chunk))
            chunk = text[begin:end]
            parts.append(("macro", chunk))
            index = end
        if text[index:]:
            parts.append(("text", text[index:]))
        return parts

    def build_match_tree(self, parts):
        """
        Build a tree from the parts returned by split_text.  Returns a list
        of items.  Nested lists are supposed to start and end with an
        opening/closing macro.  "Singular" macros are allowed inside lists
        as well.
        """
        stacks = [[]]
        for part in parts:
            type, text = part
            if type == 'text':
                stacks[-1].append(part)
            elif type == 'macro':
                if text.startswith('{+'):
                    stacks.append([])
                    stacks[-1].append(part)
                elif text.startswith('{-'):
                    startmacro = stacks[-1][0][1]
                    # closing macro should be the same as opening macro
                    if text[2:] != startmacro[2:]:
                        raise UnbalancedMacroError, part
                    stacks[-1].append(part)
                    z = stacks.pop()
                    stacks[-1].append(z)
                else:
                    # it's a normal macro
                    stacks[-1].append(part)
            else:
                raise MacroError, "Unknown type: %s" % (part,)
        #
        if len(stacks) > 1:
            raise UnbalancedMacroError, stacks[-1]
        #
        return stacks[0]

    def expand_tree(self, tree):
        """
        Expand a tree as returned by build_match_tree.  Returns a string
        with macros expanded if possible.  Any nested macros are expanded
        first, then passed up the evaluation tree as strings.
        """
        parts = []
        for elem in tree:
            if isinstance(elem, list):
                assert len(elem) >= 2
                assert elem[0][0] == elem[-1][0] == 'macro'
                assert elem[0][1][2:] == elem[-1][1][2:]
                # text between + and -, expanded
                z = self.expand_tree(elem[1:-1])
                expanded = self.eval_macro(elem[0][1], z)
                parts.append(expanded)
            elif isinstance(elem, tuple):
                type, text = elem
                if type == 'text':
                    parts.append(text)
                elif type == 'macro':
                    assert not (text.startswith("{+") or text.startswith("{-"))
                    expanded = self.eval_macro(text)
                    parts.append(expanded)
                else:
                    raise MacroError, elem
            else:
                raise MacroError, elem
        #
        return ''.join(parts)

    def eval_macro(self, macrotext, spanned_text=""):
        """
        Evaluate a macro.  <macrotext> is a string like '+upper' or
        'url'.  Curly braces are allowed around it.
        """
        original_macrotext = macrotext
        if macrotext.startswith("{") and macrotext.endswith("}"):
            macrotext = macrotext[1:-1]
        parts = macrotext.split(";")
        # args may be empty
        name, args = parts[0], parts[1:]
        #
        # get the name of the function/object that we're going to call
        fname = name
        if name.startswith("+") or name.startswith("-"):
            fname = name[1:]
            args.append(spanned_text) # add enclosed text as last parameter
        #
        try:
            f = self.namespace[fname]
        except KeyError:
            return original_macrotext
            # if macro not found, return the literal text
            # this MAY change later, or might be set as an option
        #
        if fname == name:
            # a "singular" macro (no + or -)
            if callable(f):
                return str(f(*args))
            else:
                return str(f)   # for string literals etc
        elif name.startswith("+"):
            return str(f().open(*args))
        elif name.startswith("-"):
            return str(f().close(*args))

    #
    # toplevel method

    def expand(self, text):
        """
        Return text with macros expanded.
        """
        matches = self.find_macros(text)
        parts = self.split_text(text, matches)
        tree = self.build_match_tree(parts)
        return self.expand_tree(tree)


def replace_all(text, macro_ns, ignore_errors = 0):
    tm = TextMacros(macro_ns)
    return tm.expand(text)

"""
CHANGELOG

2005/06/18
Changes by Nicola Larosa
    Code cleanup
        lines shortened
        comments on line above code
        empty comments in empty lines

2005/05/30
Removed use of string module.

"""

