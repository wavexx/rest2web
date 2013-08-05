# embedded_code.py

# Subversion Details
# $LastChangedDate: 2006-11-19 22:39:20 +0100 (Sun, 19 Nov 2006) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web/embedded_code.py $
# $LastChangedRevision: 226 $

# The templating engine for rest2web
# http://www.voidspace.org.uk/python/rest2web

# Adapted from Firedrop2 by Hans Nowak
# http://zephyrfalcon.org

# Copyright Michael Foord & Hans Nowak, 2004 & 2005.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates, and support, please join the
# Pythonutils mailing list.
# http://groups.google.com/group/pythonutils/
# Comments, suggestions, and bug reports, welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk

__all__ = (
    'render',
    'render_well',
    'render_value_eval',
    'render_value_exec',
    'get_indentation',
    'replace_separators',
    'align_multiline_code',
)

import re
import StringIO
import sys
import traceback

_generic = "\<\%c.*?\%c\>"
_markers = []
_uservalues_markers = []
_MAX = 100

def _build_generic(char, uservalues=False):
    if len(char) != 1:
        raise ValueError("Can only build parsers for a single character.")
    pattern = _generic % (char, char)
    if not uservalues:
        _markers.append('<%s' % char)
    else:
        _uservalues_markers.append('<%s' % char)
    return re.compile(pattern, re.MULTILINE|re.DOTALL)

re_code_userval_eval = _build_generic('*', True)
re_code_userval_exec = _build_generic('$', True)
re_code_eval = _build_generic('%')
re_code_exec = _build_generic('#')


def render(template, namespace, uservalues=False, final_encoding=None):
    """Render all embedded code, both single value and multiline code."""
    if not uservalues:
        regexes = (re_code_exec, re_code_eval)
    else:
        regexes = (re_code_userval_exec, re_code_userval_eval)
    #
    for (fun, regex) in zip((render_value_exec, render_value_eval), regexes):
        occs = re.findall(regex, template)
        for occ in occs:
            value = fun(occ, namespace)
            # FIXME: Should this be restricted to a single replace for each run
            #   through ?
            if isinstance(value, unicode) and final_encoding:
                value = value.encode(final_encoding)
            template = template.replace(occ, value)
    return template

def render_well(template, namespace, uservalues=False, final_encoding=None):
    if uservalues:
        markers = _uservalues_markers
    else:
        markers = _markers
    i = 0
    while i < _MAX:
        # Max 100 iterations
        i += 1
        template = render(template, namespace, uservalues,final_encoding=final_encoding)
        # evaluates to False if no markers found
        if not [True for m in markers if m in template]:
            break
    return template

def render_value_eval(code, namespace):
    """
    Render code, in the form of a string "<% something %>", to its value by
    evaluating (gasp!) it."""
    code = code[2:-2].strip()
    try:
        value = eval(code, namespace)
    except Exception, e:
        e.namespace = namespace
        raise
    return "%s" % (value,)

def render_value_exec(code, namespace):
    """
    A bit more complex than render_value_eval. We redirect sys.stdout to a
    StringIO, so anything written to (the fake) sys.stdout, or printed, is
    caught by it and placed in HTML instead. Name 'doc' is available as a
    shorthand for sys.stdout.
    
    Note that multi-line code should start on a separate line:
    <#
       print this
       print that
    #>
    """
    s = StringIO.StringIO()
    oldstdout, sys.stdout = sys.stdout, s
#    code = restyle_code(code[2:-2].strip())
    # remove <# #>
    code = code[2:-2]
    code = replace_separators(code)
    code = align_multiline_code(code)
    if not code.endswith('\n'):
        code += '\n'
    #
    try:
        codeobj = compile(code, '<string>', 'exec')
    except Exception, e:
        print >> sys.stderr, "Error in compiling template code."
        print >> sys.stderr, str(code)
        raise e
    #
    namespace["doc"] = sys.stdout 
    # for printing tracebacks etc
    namespace['stdout'] = oldstdout
    try:
        try:
            exec codeobj in namespace
        except Exception, e:
            # FIXME: provide better traceback information here.
            #   like line-number or context
#            print >> sys.stderr, "-----An error occurred:-----"
#            traceback.print_exc() 
#            print >> sys.stderr, "code:", `code`
#            print >> sys.stderr, "----------------------------"
            e.namespace = namespace
            raise
    finally:
        sys.stdout = oldstdout
    #
    return s.getvalue()


# for some reason, \r\n as line ending is not acceptable for exec...
# so we convert that:
def replace_separators(code):
    """Replace \r\n and \r line separators with \n."""
    return code.replace('\r\n', '\n').replace('\r', '\n')

def align_multiline_code(code):
    """
    Align multi-line code so Python can execute it without running into
    inconsistent indentation.
    """
    lines = code.split("\n")
    #
    # if there's only one line, strip it
    if len(lines) == 1:
        lines[0] =lines[0].strip()
    #
    # dedent as much as possible so at least some lines end up at position 0
    ##indent = find_common_indentation(lines)
    common_indent = 9999
    for i in range(len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        lines[i] = line.replace('\t', '    ')
        common_indent = min(get_indentation(line), common_indent)
    for i in range(len(lines)):
        lines[i] = lines[i][common_indent:]
    #
    # glue everything back together and hope for the best ;-)
    return "\n".join(lines)

def find_common_indentation(lines):
    """
    Find the minimum indentation that all lines have.  Ignore empty lines.
    """
    common_indent = 9999
    for line in lines:
        if not line.strip():
            # ignore empty lines
            continue
        indent = get_indentation(line)
        if indent < common_indent:
            common_indent = indent
    return common_indent

def get_indentation(line):
    """Get a string's indentation."""
    indent = 0
    for c in line:
        if c == " ":
            indent += 1
        else:
            break
    return indent


if __name__ == "__main__":
    #
    code = """\
Hi! My name is <% name %>. Pleased to meet ya,
I'm a funky creature.
Let's print some numbers, eh?
<#
for i in range(5):
    print i
#>
<% signature %>
"""
    #
    name = "Hans"
    signature = "--\nhans@nowak.com"
    #
    print render(code, globals())


"""
TODO
====

Mixed tab/space indentation breaks this.

CHANGELOG
=========

2006/08/06
Exec done before eval in render_well.

2006/04/15
Added the handling of uservalues in ``render``.

Generalised the ``render`` function and added the ``_build_generic`` function
for creating the various regular expressions.

2005/06/18
Changes by Nicola Larosa
    Code cleanup
        lines shortened
        comments on line above code
        empty comments in empty lines

2005/06/06
Removed extraneous print statement.

2005/05/15
Added 'stdout' to the namespace in ``render_value_exec``
We compile the code to a codeobj in ``render_value_exec``
Replaced use of the string module with string methods.


TODO/ISSUES
Can we improve the error messages ?
    (e.g. the line in the template they occur in ?)

We *could* use ``eval`` in ``render_value_exec``, (for single line statements only)
    and so eliminate the distinction between '<# ... #>' and '<% .... %>'
    (This would prevent us from exec'ing single line fucntion calls though)

Should tabsize be a config option ? (in ``get_indentation``)
"""

