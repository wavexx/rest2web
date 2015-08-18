# restindex.py

# Subversion Details
# $LastChangedDate: 2007-06-10 00:06:55 +0200 (Sun, 10 Jun 2007) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web/restindex.py $
# $LastChangedRevision: 246 $

# The function that parses the restindex, and associated data.
# http://www.voidspace.org.uk/python/rest2web

# Copyright Michael Foord, 2004 - 2006.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates and support, please join the
# rest2web mailing list.
# http://lists.sourceforge.net/lists/listinfo/rest2web-develop
# Comments, suggestions and bug reports welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk


import os
from rest2web.embedded_code import align_multiline_code


class restindexError(SyntaxError):
    """ """


# acceptable values for keywords that must be on or off
true_false_list = ['yes', 'no', 'true', 'false', 'on', 'off', '1', '0']

# keywords that are on or off
true_false_keywords = ['include', 'build', 'typogrify']

# any keywords that take normal text values
text_keywords = [
    'file-extension', 'template', 'index-file', 'section',
    'link-title', 'page-title', 'crumb', 'target', 'encoding',
    'output-encoding', 'template-encoding', 'file', 'initialheaderlevel'
    ]

# keywords in this dictionary can only have values from a list of options
limited_keywords = {
    # FIXME: add sextile and textile
    'format': ['html', 'rest']
    }

# keywords in this dictionary have multiple values
# the entry is either the number of values expected
# or 0, meaning unspecified
# or a minus number meaning a *minimum* number
multiple_keywords = {'sectionlist': 0, 'section-title': 2,
                    'tags': 0, 'plugins': 0, 'section-pages': -1}

# keywords in this dictionary are descriptions
# they may also have a value assciated with them
# their entry is True or False - whether they have a value or not
# if they do, there may be multiple - and the value becomes part of the key
# (as a tuple)
description_keywords = {'section-description': 1, 'page-description': 0}

# keywords that can appear more than once
repeat_keywords = [
                    'section-title', 'section-description', 'file',
                    'section-pages', # 'nofile', 'filemask',
                    ]


def remove_comment(inlines):
    restindex = inlines[1:]
    indent = 0
    i = -1
    while i < len(restindex):
        i += 1
        line = restindex.pop(0)
        stripped = line.strip()
        if not stripped:
            continue
        this_indent = len(line) - len(stripped)
        if indent and this_indent < indent:
            return inlines
        indent = min(this_indent, indent or this_indent)
        if stripped == 'restindex':
            restindex.insert(0, line)
            break
    else:
        return inlines
    #
    return restindex


def find_start(inlines):
    while inlines:
        line = inlines.pop(0)
        if not line.strip():
            continue
        if line.strip().startswith('..') and  line.find('::') == -1:
            inlines.insert(0, line)
            inlines = remove_comment(inlines)
            break
        inlines.insert(0, line)
        break
    return inlines


def read_restindex(infile):
    """
    Interpret the restindex and divide it from the contents.
    
    Given a file as a list of lines (or file object, or bounded iterable),
    read the restindex from the start. (if any)
    Returns restindex, remainder of file (which will have trailing whitespace
    removed from each line).
    restindex will be None if there isn't one.
    
    If it finds any errors it raises ``restindexError`` - which is a subclass
    of ``SyntaxError``
    """
    # FIXME: consumes the whole file immediately
    thefile = [line.rstrip() for line in infile]
    thefile.append('')
    #
    # UTF8 BOM
    if thefile[0].startswith('\xef\xbb\xbf'):
        # get rid of it
        thefile[0] = thefile[0][3:]
    #
    thefile = find_start(thefile)
    #
    started = False
    indesc = False
    thisdesc = []
    restindex = {}
    #
    index = -1
    length = len(thefile) - 1
    # indexing like this is more versatile, we can manually
    # wind forwards or back
    while index < length:
        index += 1
        origline = thefile[index]
        line = origline.strip()
        #
        if (line and
                not line.startswith('#') and
                not line == 'restindex' and
                not line.strip() == '..' and
                not started
                ):
            return None, '\n'.join(thefile)
        #
        # if we are in a multiline value
        if indesc:
            # end of a description
            if not line == '/description':
                thisdesc.append(origline)
            else:
                # join, remove indentation, and save
                value = align_multiline_code('\n'.join(thisdesc))
                # FIXME: special case for 'section-description' -
                # where indesc is a tuple
                if isinstance(indesc, tuple):
                    keyword, name = indesc
                    if restindex.has_key(keyword):
                        if restindex[keyword].has_key(name):
                            # section description twice
                            raise restindexError(('"%s" repeated for "%s"'
                                ' - line %s') % (keyword, name, index + 1))
                        restindex[keyword][name] = value
                    else:
                        restindex[keyword] = {name: value}
                else:
                    restindex[indesc] = value
                indesc = None
                thisdesc = []
            continue
        #
        if line.startswith('#') or not line:
            # comments and empty lines are skipped
            continue
        #
        if not started and line.strip() == '..':
            continue
        #
        if line == 'restindex':
            if started:
                raise restindexError(('restindex found in the wrong place'
                    ' - line %s') % (index + 1))
            started = True
            continue
        #
        if line == '/restindex':
            # the end
            body = [''] * (index+1) + thefile[index+1:]
            return restindex, '\n'.join(body)
        #
        if line.find(':') == -1:
            raise restindexError('No keyword on line - line %s' % (index + 1))
        keyword, value = line.split(':', 1)
        keyword = keyword.strip().lower()
        value = value.strip()
        #
        if restindex.has_key(keyword) and keyword not in repeat_keywords:
            raise restindexError('Keyword "%s" repeated - line %s' % (
                keyword, index + 1))
        #
        if keyword in true_false_keywords:
            # this keyword should be on or off
            value = value.lower()
            if value not in true_false_list:
                raise restindexError('Strange value - line %s' % (index + 1))
            restindex[keyword] = value
            continue
        #
        if keyword in text_keywords:
            if keyword in repeat_keywords:
                try:
                    restindex[keyword].append(value)
                except KeyError:
                    restindex[keyword] = [value]
            else:
                # this keyword takes a straight text value
                restindex[keyword] = value
            continue
        #
        if keyword in limited_keywords:
            # value must be one from a list of options
            value = value.lower()
            if value not in limited_keywords[keyword]:
                raise restindexError, 'Strange value - line %s' % (index + 1)
            restindex[keyword] = value
            continue
        #
        if keyword in multiple_keywords:
            # NOTE we can have multiple section titles
            numsplits = multiple_keywords[keyword]
            if numsplits < 1:
                if not value:
                    values = []
                else:
                    values = [entry.strip() or None
                                    for entry in value.split(',')]
                if numsplits < 0:
                    numsplits = int(numsplits)
                    if len(values) < numsplits:
                        raise restindexError(('Multiple keyword with too '
                                        'few values - line %s') % (index + 1))
                if keyword in repeat_keywords:
                    # keyword is a repeat
                    # first value is a name
                    name = values[0]
                    values = values[1:]
                    if restindex.has_key(keyword):
                        if restindex[keyword].has_key(name):
                            raise restindexError(('"%s" repeated for "%s"'
                                ' - line %s') % (keyword, name, index + 1))
                        restindex[keyword][name] = values
                    else:
                        restindex[keyword] = {name: values}
                #
                else:
                    restindex[keyword] = values
            else:
                values = [entry.strip() or None
                    for entry in value.split(',', numsplits-1)]
                name = values[0] or None
                # this allows UP TO numsplit values - XXXX *doesn't* choke
                # on less; NOTE: returns a list, even though will usually
                # be 0 or 1 items
                value = values[1:]
                if numsplits == 2:
                    # special case - should only have a single value
                    if value:
                        value = value[0]
                    else:
                        value = ''
                if restindex.has_key(keyword):
                    # section description twice
                    if restindex[keyword].has_key(name):
                        raise restindexError(('"%s" repeated for "%s"'
                            ' - line %s') % (keyword, name, index + 1))
                    restindex[keyword][name] = value
                #
                else:
                    restindex[keyword] = {name: value}
            continue
        #
        if keyword in description_keywords:
            if description_keywords[keyword]:
                indesc = (keyword, value or None)
            else:
                indesc = keyword
            continue
        #
        # if we get this far, we haven't recognised the keyword
        # FIXME: show the offending line?
        raise restindexError('Unrecognised keyword - line %s' % (index + 1))
    # if we get this far, we reached the end of the file
    # without finding '/restindex'
    if not started:
        return None, '\n'.join(thefile)
    raise restindexError, "No '/restindex' found."

default_restindex = {
    'include': 'yes',
    'format': 'rest',
    'file-extension': 'html',
    'template': None,
    'index-file': 'index.txt',
    'template-encoding': None,
    'section': None,
    'link-title': '',
    'page-title': None,
    'page-description': '',
    'crumb': None,
    'target': None,
    'build': 'yes',
    'sectionlist': [],
    'section-title': {},
    'section-description': {},
    'encoding': None,
    'output-encoding': None,
    'tags': [],
    'section-pages': {},
    'plugins': [],
    'typogrify': 'yes',
    'file': [],
#    'filemask': [],
#    'nofile': [],
    'initialheaderlevel': '1'
}

# these keyword(s) set the default value for the whole directory
default_keywords = ['file-extension', 'initialheaderlevel']

if __name__ == '__main__':
    ri = """
restindex
    # this is a comment
        include: yes
        file: file1
        file: file2
        file: file3
        plugins:
        format: html
        tags: tag1, tag2, tag3
        file-extension: shtml
        template: template.txt
        template-encoding: utf8
        index-file: index.txt
        section:  section name
        link-title: This is the text to use in the link
        page-title: We *usually* only need a title for HTML
        page-description:
            this is a description
            It can go across several line
            And even be indented a bit.
            It will be interpreted as *reST*.
        /description
        crumb: Short Name
        build: yes
        target: thisfile.html
        encoding: utf8
        output-encoding: utf8
        sectionlist: , section-name, section-name2, section-name3
        section-title: section-name, title
        section-description: section-name
            This is also a description.
        
        /description
        section-title: , default-section-title
        section-description:
            This is the default-section description.
        
        /description
        section-pages: , page1, page2, page3
        section-pages: section-name, page1, page2, page3
/restindex
"""
    rest_index = read_restindex(ri.split('\n'))[0]
    for entry in rest_index:
        print entry, '  :  ', rest_index[entry]

    #
    ri2 = """
..
    restindex
        # this is a comment
            include: yes
            file: file1
            file: file2
            file: file3
            plugins:
            format: html
            tags: tag1, tag2, tag3
            file-extension: shtml
            template: template.txt
            template-encoding: utf8
            index-file: index.txt
            section:  section name
            link-title: This is the text to use in the link
            page-title: We *usually* only need a title for HTML
            page-description:
                this is a description
                It can go across several line
                And even be indented a bit.
                It will be interpreted as *reST*.
            /description
            crumb: Short Name
            build: yes
            target: thisfile.html
            encoding: utf8
            output-encoding: utf8
            sectionlist: , section-name, section-name2, section-name3
            section-title: section-name, title
            section-description: section-name
                This is also a description.
            
            /description
            section-title: , default-section-title
            section-description:
                This is the default-section description.
            
            /description
            section-pages: , page1, page2, page3
            section-pages: section-name, page1, page2, page3
    /restindex
"""
    print
    print
    print 'Attempting restindex in a comment:'
    print
    rest_index2 = read_restindex(ri2.split('\n'))[0]
    for entry in rest_index2:
        print entry, '  :  ', rest_index[entry]
    assert rest_index == rest_index2

# multiline parser
# for uservalues

import re

valid_line = re.compile(r'\s*([a-zA-Z_]\w*)\s*(?:=|:)(.*)')
# the reserved_names are all the names used in the namespace other than 'body'
reserved_names = [
    'title', 'breadcrumbs', 'sections', 'pagename', 'pagepath',
    'encoding', 'output_encoding', 'final_encoding', 'path_to_root',
    'sectionlist', 'rest_dict', 'doc', 'stdout', 'modified', 'modtime',
    'template_file', 'template_encoding', 'indexpage', 'indextree',
    'thispage', 'sidebar', 'minibar', 'print_crumbs', 'Processor', 'tags',
    'default_section', 'modtime', 'modtimeiso'
    ]

def parse_user_values(content, directory):
    """
    Read the content of a page, as a list of lines (after the restindex
    has been read). Parse and extracts any 'uservalues'

    Return (uservalues, content) - (dict, string)
    uservalues will be ``None`` if there is no uservalues section.
    """
    quot = ''
    user_values = {}
    found_end = False
    started = False
    index = -1
    length = len(content) - 1
    while index < length:
        index += 1
        line = content[index]
        #
        if quot:
            val = val + '\n'
            if line.rstrip().endswith(quot):
                val += line.rstrip()[:-3]
                quot = False
                user_values[name] = val
            else:
                val += line
            continue
        #
        if line.lstrip().startswith('#') or not line.strip():
            continue
        elif not started and line.strip() == 'uservalues':
            started = True
            continue
        elif not started:
            return None, '\n'.join(content)
        #
        # XXXX if we find a '/uservalues' without a start
        # XXXX should we raise an error ?
        elif line.strip() ==('/uservalues'):
            found_end = True
            break
        #
        mat = valid_line.match(line)
        if not mat:
            raise SyntaxError, 'Invalid line in uservalues:\n    "%s"' % line
        name, val = mat.groups()
        if name in reserved_names:
            raise SyntaxError, ('Use of reserved name in uservalues:\n'
                '    "%s"') % line
        if val.lstrip()[:3] in ['"""', "'''"]:
            quot = val.lstrip()[:3]
            val = val.lstrip()[3:]
            if val.rstrip().endswith(quot):
                quot = ''
                val = val.rstrip()[:-3]
            else:
                continue
        user_values[name] = val.strip()
    #
    if not started:
        # only blank lines or comments
        return None, '\n'.join(content)
    if quot:
        raise SyntaxError, 'No end to a triple quoted section.'
    if not found_end:
        raise SyntaxError, 'No end to "uservalues" section.'
    #
    content = content[index+1:]
    if user_values.has_key('body'):
        loc = os.path.normpath(os.path.join(directory, user_values['body']))
        # XXXX os.path.join ? technically this value will be in URL form
        # - not native
        #
        content = open(loc).readlines()
        del user_values['body']
    #
    return user_values, '\n'.join(content)

#######################################################################

if __name__ == '__main__':
    print
    print '#'*30
    print
    #
    content1 = '''
    
    #comment
    
    uservalues
        test: 3
        # a comment
        test2: a value
        test3 = \''' a multiline
    """ value"""
    \'''
        test4 = """ A test """
        test5 = """
        
        A long
        line.
        """
    /uservalues
    
    The content...
'''
    
    content2 = '''
    
    uservalues
    test = """
    
    /uservalues
    '''
    directory = ''
    (user_values, content) = parse_user_values(
        content1.split('\n'), directory)
    print 'Content: ', content
    for entry in user_values:
        print entry, '  :  ', user_values[entry]
    #
    try:
        (user_values, content) = parse_user_values(
            content2.split('\n'), directory)
    except SyntaxError:
        print 'Picked up the error in content2.'
    else:
        print '***FAIL** failed to pick up the error in content2.'
        raise SyntaxError
    


"""
CHANGELOG
=========


2006/08/13
----------

Allow the restindex and uservalues to be in a ReST comment.


2005/10/12
----------

Added the 'section-pages' keyword. Only valid for indexes.


2005/07/26
Added 'file' and 'plugins' keywords
Added 'tags' to reserved name
An empty multiple value now returns '[]' rather than '[None]'


2005/07/23
Added the tags keyword.


2005/06/18
Changes by Nicola Larosa
    Code cleanup
        lines shortened
        comments on line above code
        empty comments in empty lines


2005/06/12
Added the parser for "uservalues"


2005/05/20
Added the 'template-encoding' keyword.
Allowed for default section in sectionlist.


2005/05/16
restindex['section-title'] is now a dictionary of single values, rather than a
dictionary of lists !


2005/05/15
``read_restindex`` removes UTF8 BOM at start of files
Added ``output-encoding`` keyword.
If no name is given with a section-description, then we use ``None`` (the default section)
A ``section-title`` with no name (``section-title: , Title Line``) is a title for the default section.
Added test.

"""
