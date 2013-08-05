# functions.py

# Subversion Details
# $LastChangedDate: 2007-04-04 17:48:50 +0200 (Wed, 04 Apr 2007) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web/functions.py $
# $LastChangedRevision: 245 $

# The standard functions for use in templates
# A part of rest2web
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
import urllib

__all__ = (
        'sidebar',
        'print_crumbs',
        'minibar',
        'print_details',
        'section_contents',
        'formattime',
        'include',
            )

uservalues = {}
namespace = {}

def _set_uservalues(n, u):
    """Set the namespace and uservalues for the page."""
    global namespace
    global uservalues
    uservalues = u
    namespace = n


def formattime(t=None, format="%a, %d %b %Y %H:%M:%S"):
    """
    Given a time in seconds since the epoch (e.g. the ``modified`` value),
    convert it into a time formatted using the ``time.strftime`` function.
    
    See the docs at http://docs.python.org/lib/module-time.html for how to
    create format strings.
    
    The default format string is ``"%a, %d %b %Y %H:%M:%S"``. This produces
    dates that look like :
    
        ``'Fri, 27 Jan 2006 09:53:52'``
    
    If you don't supply a time, then the current time is used. The time is
    always understood as a *local time*.
    """
    import time
    return time.strftime(format, time.localtime(t))


def sidebar(
        thetree,
        div = '<div style="margin:10px">',
        undiv = '</div>',
        cmp = None):
    """
    A generator for dealing with the ``'indextree'`` of pages and indexes.
    
    It is recursive for handling the nested 'branches' of the tree.
    
    It goes through all the pages from the top level of the tree 
    provided. 
    
    It yields pages one at a time - index page first. (It sets ``page['title'] = True`` 
    on index pages - otherwise  ``page['title'] = False``. This allows you to 
    display them differently).
    
    Before moving down the tree it prints a value called ``'div'`` after finishing
    a branch it prints 'undiv'.
    
    Default value for div is ``'<div style="margin:10px">'``.
    
    Default value for undiv is ``'</div>'``.
    
    You would typically use this in a template with something like :
    
    .. raw:: html
    
        {+coloring}
        
        for page in sidebar(indextree):
            val = page['crumb']
            link = page['target']
            if page['title']:
                print '<br /><strong><a href="%s">%s</a></strong>' \
                % (link, val)
            else:
                print '<br /><a href="%s">%s</a>' % (link, val)
        
        {-coloring}
            
    It might be more sensible to pass in a div with a named class. This makes it 
    easier to control the style through CSS. For example 
    ``for page in sidebar(indextree, '<div class="sidebar-links">'):``.
    
    You can pass in an optional compare function to sort the pages. An example sort function,
    sorting by crumb:
    
        ``cmp_page = lambda page1, page2 : cmp(page1['crumb'], page2['crumb'])``
    
    You could also have (for example) a date uservalue in each page and sort on the date.
    """
    print div
    thetree['title'] = True
    yield thetree
    page_list = thetree['pages']
    if cmp is not None:
        page_list.sort(cmp=cmp)
    for page in page_list:
        if page['pages']:
            for entry in sidebar(page, div=div, undiv=undiv, cmp=cmp):
                yield entry
        else:
            page['title'] = False
            yield page
    print undiv


def print_crumbs(
        breadcrumbs,
        item = '<li>%s</li>',
        anchor = '<a href="%s">%s</a>',
        divider = '&gt;',
        ):
    """
    A function to print the breadcrumbs (navigation) trail for a page.
    
    The idea is that all the index pages above the current page are shown as 
    links. There are dividers in between, and the crumb of the current page is
    shown (but not as a link).
    
    You pass in the breadcrumbs values. It needs an item value with one ``'%s'`` 
    place holder. Every link and divider (and the last value) is put into this item.
    The default value is ``'<li>%s</li>'``.
    
    It needs an anchor value with two ``'%s'`` placeholders. Into this are inserted 
    the link and the 'crumb'. The default value is ``'<a href="%s">%s</a>'``
    The last crumb is printed without the use of the ``'anchor'`` value.
    
    It also needs a divider which is printed between the crumbs.
    The default value is ``'>'``. If you set the divider to ``None``, then no dividers
    will be printed between crumbs.
    
    By default this function uses list items to display the crumbs.
    
    You should surround it using something like : ::
    
        '<div id="crumbs"><ul>...</ul></div>'
    
    Then use css rules like the following to format the display of the crumbs : ::
        
        #crumbs {
            background-color:#c99;
            padding:5px;
            text-align:center;
            font-size:15pt;
            font-weight:bold;
        }
        
        #crumbs ul {
            margin:0;
            padding:0
        }
        
        #crumbs li {
            display:inline;
            list-style:none;
            margin:0;
            padding:5px;
        }
    
    So to display the breadcrumbs trail without using list items, you could put the 
    following in your template : ::
    
        <# 
            # item no longer uses ``<li>``
            item = '%s'
            print_crumbs(breadcrumbs, item=item)
        #>
    """
    # this is the breadcrumbs code
    # breadcrumbs is a list of tuples
    index = -1
    while index < len(breadcrumbs)-2:
        index += 1
        entry = breadcrumbs[index]
        print (item % (anchor % entry))
        if divider is not None:
            print (item % divider)
    if breadcrumbs:
        # not as a link
        print (item % (breadcrumbs[-1][1]))


def minibar(
        sections,
        item = '<li><a href="%s">%s</a></li>',
        intro = '<h3>Pages</h3>',
        subsect = True,
        subintro = '<h3>Sub Sections</h3>',
        liststart = '<ul>',
        listend = '</ul>',
        displayval = 'link-title'):
    """
    This function prints an alternative sidebar to the 'sidebar' function.
    
    It uses the ``'sections'`` value rather than indextree and only goes 
    through the pages in the current directory.
    
    It can optionally differentiate between pages that are themselves 
    'subsections' (index pages for sections below) and ordinary pages.
    
    You need to pass in the 'sections' value, as well as any of the following 
    optional keyword arguments :
    
    If ``'subsect'`` is ``True`` (the default) then minibar divides pages 
    into ordinary pages and 'subsections'. Otherwise they're all pages.
    
    If there are any pages then the value 'intro' is printed. Default is ``'<h3>Pages</h3>'``.
    
    Then liststart is printed. Default is ``'<ul>'``.
    
    The for each page the following is printed : ::
    
        item % (page['target'], page[displayval])
        
    The default for item is ``'<li><a href="%s">%s</a></li>'``
    
    The default for displayval is ``'link-title'``. (It should be one of the values
    stored in each page. An alternative value would be ``'crumb'``).
    
    Then listend is printed. Default is ``'</ul>'``.
    
    If there are any subsections (and ``'subsect'`` is ``True``) then value 
    ``'subintro'`` is printed. Default is ``'<h3>Sub Sections</h3>'``
    
    Then the same sequence as for pages is printed : ::
    
        list start, the page links, listend
    
    Note: it doesn't include a link to the index page in a section. You will need 
    to include this yourself separately.
    """
    sub_sections = []
    pages = []
    for section_name in sections:
        section = sections[section_name]
        for page in section['pages']:
            if not subsect or not page['subdir']:
                pages.append(page)
            else:
                sub_sections.append(page)
    #
    if pages:
        print intro
        print liststart
        for page in pages:
            print item % (page['target'], page[displayval])
        print listend
    #
    if sub_sections:
        print subintro
        print liststart
        for page in sub_sections:
            print item % (page['target'], page[displayval])
        print listend


def section_contents(section, split=True):
    """
    Passed in a section - this function returns the pages and subsections.
    
    Each page (or subsection) is returned as a tuple :
    (url, link title, description)
    
    The urllib is escaped for putting straight into the link.
    
    If split is True (the default) this function returns a list of pages and a
    list of subsections.
    
    If split is False it just returns a single list.
    
    An example use of this function might be :
    pageblock = '''\
            <li><a href="%s">%s</a>
                <p>%s</p>
            </li>
    '''
    # just use the default section
    pages, subsections = section_contents(sections[None])
    # first print the pages
    if pages:
        print '<h3>Pages</h3>'
        print '<ul>'
        for page in pages:
            print pageblock % page
        print '</ul>'
    # next - the subsections
    if subsections:
        print '<h3>Subsections</h3>'
        print '<ul>'
        for page in subsections:
            print pageblock % page
        print '</ul>'
    """
    pages = []
    subsections= []
    for page in section['pages']:
        entry = (urllib.quote(page['target']), page['link-title'],
                                                    page['page-description'])
        if page['subdir'] and split:
            subsections.append(entry)
        else:
            pages.append(entry)
    if split:
        return (pages, subsections)
    else:
        return pages


def print_details(section,
            page_title='<h3>Pages</h3>',
            subsection_title='<h3>Sub Sections</h3>',
            item_wrapper = '<ul>%s</ul>',
            item='<li>%s</li>',
            link='<a href="%s">%s</a>',
            description='%s',
            do_description=True,
            split=True,
            do_pages=True,
            do_subsections=True,
            wrapper_class=None,):
    """
    This function is a quick way of printing all the pages and sub-sections in
    a section. You can use it without having to understand the ``sections``
    data structure.
    
    It prints a menu of all pages (links and descriptions) and sub-sections.
    
    It has sensible defaults - and is configurable in terms of the HTML used.
    
    Including the description of each page is optional.
    
    You can also elect to do pages and subsections combined, separately, or
    just one or the other.
    
    Like the other function it needs "%s" in some of the values - which are
    filled in automatically.
    
    The containing ``div`` will *only* be present if you pass a value for
    ``wrapper_class``. In this case the value you pass in will be the class
    attribute of the ``div``.
    
    The default layout looks like : ::
    
        <div class="wrapper_class>      ---> Only present if used
        <h3>Page Title</h3> ---> ``page_title``
        
        <ul> ---> ``item_wrapper`` along with the corresponding ``</ul>``.
                  This wraps all the links.
            <li> ---> ``item`` along with the corresponding ``</li>``. This
                      wraps each item - whether or not it includes the
                      description.
            <a href="url">Link Title</a> ---> ``link``. This contains the URL
                                              *and* the link title.
            Page description. ---> ``description`` . Optional,
                                           controlled by ``do_description``
            </li>
        </ul>
        </div>  ___> Only present with ``wrapper_class``.
    
    This is then repeated for the subsections. If ``split`` is ``False`` then
    all the pages and subsections are combined as the pages.
    
    The options are :
        page_title = '<h3>Pages</h3>'
        
            This is the title line printed before the pages.
        
        subsection_title = '<h3>Sub Sections</h3>'
        
            This is the title line printed before the Sub Sections.
        
        item_wrapper = '<ul>%s</ul>'
        
            This is the wrapper around all the links. It needs one "%s" in it.
        
        item = '<li>%s</li>'
        
            This is the wrapper around each link. It needs one "%s" in it.
        
        link = '<a href="%s">%s</a>'
        
            This is the link. It needs two "%s" in it.
    
        description = '%s'
        
            This is for the description and is put immediately after the link.
            It needs one "%s" in it. You could put a tags around the 
            description to style them separately. E.g. 
            ``description = '<div class="description>%s</div>'``).
            
            .. note::
            
                It's not necessary to explicitly put paragraph tags around the
                description.
                
                **rest2web** renders descriptions using `docutils <http://docutils.sf.net>`_
                which does this automatically.
        
        do_description = True
        
            If ``True``, the description is added to each link.
        
        split = True
        
            If ``True``, the pages are done separately from the sub-sections.
        
        do_pages = True
        
            If ``False``, the pages are not printed.
        
        do_subsections = True
        
            If ``False``, the subsections are not printed.
        
        wrapper_class = None
        
            If you pass in a value for this, the output is enclosed in a
            ``div``. The class attribute is set to the value you specify here.
    """
    if wrapper_class:
        print '<div class="%s">' % wrapper_class
    if split:
        pages, subsections = section_contents(section, split=True)
    else:
        subsections = []
        pages = section_contents(section, split=False)
    #
    if pages and do_pages:
        print page_title
        entries = []
        for page in pages:
            val = link % (page[0], page[1])
            if do_description:
                val += description % page[2]
            entries.append(item % val)
        print item_wrapper % ('\n').join(entries)
    #
    if subsections and do_subsections:
        print subsection_title
        entries = []
        for page in subsections:
            val = link % (page[0], page[1])
            if do_description:
                val += description % page[2]
            entries.append(item % val)
        print item_wrapper % ('\n').join(entries)
    if wrapper_class:
        print '</div>'


def include(filename, alternative=None):
    """
    Include a file in the page or template.
    
    If the filename is not an absolute or relative
    path (just a filename), walk up the directory tree
    looking for a file to include.
    
    It returns the file as text or raises an ``IOError``.
    
    It takes an optional ``alternative`` keyword, which will be
    returned if the file is not found.
    """
    curdir = namespace['current_dir']
    path, _ = os.path.split(filename)
    if not path and '\\' not in filename and '/' not in filename:
        while True:
            newname = os.path.normpath(os.path.join(os.getcwd(), curdir, filename))
            if os.path.isfile(newname):
                filename = newname
                break
            curdir, _ = os.path.split(curdir)
            if not curdir:
                break
    elif '\\' in filename or '/' in filename:
        filename = os.path.normpath(os.path.join(os.getcwd(), curdir, filename))
    if not os.path.isfile(filename) and alternative is not None:
        return alternative
    return open(filename).read() 


"""
CHANGELOG
=========

2006/08/04
``print_crumbs`` can now take a ``None`` value for 'divider'.
``include`` function can take an optional 'alternative' argument.

2006/07/30
Added include function.

2006/01/26
Added ``wrapper_class`` to ``print_details``.
Added formattime function.

2006/01/13
Removed the two ``<br />`` from ``listend`` in minibar.

2005/10/22
Added ``print_details`` and ``section_contents`` functions.

2005/10/16
Change to the ``print_crumbs`` function. It now takes an item value.

2005/10/13
'sections' is now an ordered dictionary - so minibar doesn't need to explicitly
use the sequence attribute any more.

2005/07/23
Minibar now follows the 'sequence' attribute where relevant.

2005/06/18
Changes by Nicola Larosa
    Code cleanup
        lines shortened
        comments on line above code
        empty comments in empty lines

2005/05/28
First version - extracted from the templates.

"""

