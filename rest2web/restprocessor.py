# restprocessor.py

# Subversion Details
# $LastChangedDate: 2007-03-13 19:34:21 +0100 (Tue, 13 Mar 2007) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web/restprocessor.py $
# $LastChangedRevision: 236 $

# The processor object (etc) for rest2web
# This builds the pages and indexes from content and templates.
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


import glob
import os
import sys
import time
import datetime
from copy import deepcopy
from urllib import url2pathname
from shutil import copy2
from traceback import print_exc
from posixpath import split as posixsplit
from StringIO import StringIO

from rest2web import functions
from rest2web.functions import strip_tags
from rest2web import textmacros
from rest2web.restutils import *
from rest2web.restindex import read_restindex, default_keywords, default_restindex
from rest2web.restindex import parse_user_values
from rest2web.embedded_code import render_well
from rest2web.printing import WARN, ACTION, INFO, out
from rest2web import printing

from docutils import ApplicationError

from rest2web.pythonutils.odict import OrderedDict
from rest2web.pythonutils.pathutils import import_path
from rest2web.pythonutils.urlpath import pathjoin, relpathto, tslash

import rest2web.defaultmacros as macros

class rest2webError(Exception):
    """ """
class NoRestIndex(Exception):
    """ """

isfile = os.path.isfile
isdir = os.path.isdir
split = os.path.split
dirname = os.path.dirname
splitext = os.path.splitext
abspath = os.path.abspath
def join(*args):
    return os.path.normpath(os.path.join(*args))
# We assume os.path.splitext is cross platform :-)

__all__ = ('Processor', 'handle_sections', 'rest2webError', 'set_print')

globalValues = {}

try:
    sorted
except NameError:
    def sorted(inlist):
        newlist = list(inlist)
        newlist.sort()
        return newlist

class SectionDict(OrderedDict):

    def sortpages(self, sortorder, section=True):
        if sortorder == 'link-title':
            sortorder = lambda x, y : cmp(x['link-title'], y['link-title'])
        if section == True:
            sections = self.values()
        else:
            sections = [self[section]]
        for section in sections:
            section['pages'].sort(sortorder)

##########################################

def add_modules(ns):
    """Add a couple of modules to a namespace."""
    ns['os'] = os
    ns['sys'] = sys
    ns['globalValues'] = globalValues

##########################################

class Processor(object):
    """A processor object for building pages from content and templates."""

    def __init__(self, options, config):
        """Initialise the processor."""
        self.dir = os.curdir
        self.dir_as_list = []
        self.dir_as_url = '/'
        self.crumbdict = {}
        self.indextree = {}
        self.breadcrumbs = []
        self.templatedict = {}
        self.outputencoding = {}
        self.plugins = {}
        self.force = False
        self._template_files = {}
        self.skip_html = False
        self.last_error = None
        #
        self.get_config(config)
        self.handle_options(options)
        if self.force:
            # load the default index file
            out('Force on - loading default index and template.', INFO)
            def_dir = config['defaults_directory']
            self._default_index = open(join(def_dir, 'index.txt')).read()
            self._default_template = join(def_dir, 'template.txt')
            self.skip_html = istrue(config.get('skip_html', 'False'))
            #
            # FIXME: This is hardwired
            self._top_level_name = 'Site'


    def get_config(self, config):
        """Handle configuration options from config file."""
        start_directory = os.path.expanduser(config['start_directory'])
        target_directory = os.path.expanduser(config['target_directory'])
        compare_directory = os.path.expanduser(config['compare_directory']) or target_directory
        macrofile = os.path.expanduser(config['macros'])
        debug = istrue(config.get('DEBUG', 'False'))
        uservalues = config.get('uservalues')
        if uservalues is None:
            uservalues = {}
        else:
            uservalues = uservalues.dict()
            try:
                # FIXME: allow a 'guess' value ?
                encoding = uservalues.pop('__encoding__')
            except KeyError:
                encoding = 'ascii'
            # FIXME: WIll this choke on list and dict (subsection) values ?
            uservalues = decode(uservalues, encoding)
##        hash = config.get('hash') or None
        #
        self.start = abspath(start_directory)
        self.target = abspath(target_directory)
        self.compare = abspath(compare_directory)
        self.defaults = deepcopy(default_restindex)
        self.macrofile = macrofile
        self.config = config
        self.uservalues = uservalues or {}
        self.debug = debug
        self.macro_paths = {
            'smiley_directory': None,
            'smiley_url': '<% path_to_root %>images/smilies/',
            'emoticon_url': '<% path_to_root %>images/',
        }
        self.macro_paths.update(config.get('Macro Paths', {}))
        self.macro_paths['smiley_directory'] = self.macro_paths['smiley_directory'] or None
        self.force = istrue(config.get('force', 'False')) or istrue(config.get('Force', 'False'))
        self.skiperrors = istrue(config.get('skiperrors', 'False'))
        self.promote_headers = istrue(config.get('promote_headers', 'True'))


    def handle_options(self, options):
        """Handle command line optins."""
        self.override_template = options['template']
        if options['uservalues']:
            # Command line uservalues override config file ones
            self.uservalues.update(options['uservalues'])
        # Set self.force if set at the command line
        self.force = self.force or options['force']
        self.skiperrors = self.skiperrors or options['skiperrors']
        #
        self.typogrify = options['typogrify']
        if self.typogrify:
            global typogrify
            import typogrify.filters


    def setmacros(self, macrofile):
        """
        Set the macro related attributes.
        Import the macros module if one is specified.
        """
        self.macros = macros.__dict__
        self.macros.update(self.macro_paths)
        self.macrodir = None
        if not macrofile:
            self.macros['acronyms'] = self.macros['default_acronyms']
            return
        elif not isfile(macrofile):
            raise RuntimeError('macros file can\'t be found "%s".' % macrofile)
        else:
            try:
                mod = import_path(abspath(macrofile))
            except ImportError:
                # Should this be a fatal error ?
                raise RuntimeError('Error importing macros file "%s".' %
                    macrofile)
            else:
                self.macros.update(mod.__dict__)
                self.macros['default_acronyms'].update(self.macros.get('acronyms', {}))
                self.macrodir = abspath(dirname(macrofile))


    def execute_safely(self, function, *args, **keywargs):
            try:
                val =  function(*args, **keywargs)
            except KeyboardInterrupt:
                raise
            except Exception, e:
                if not self.skiperrors:
                    raise
                # print any error without bombing out
                # (so we can display it, then close our files nicely)
                f = StringIO()
                print_exc(file=f)
                # write error to sys.stderr rather than printing to sys.stdout
                self.last_error = f.getvalue()
                printing.ERROR_STATUS += 1
                return False
            else:
                self.last_error = None
                return val


    def output_error(self, msg):
        out(msg + '\n' + self.last_error + '\n', WARN)


    def copy_file(self, entry, filename, target, index=False):
        """Copy files from the ``file`` keyword."""
        entry = os.path.expanduser(entry)
        if not index:
            src = join(self.dir, dirname(filename), entry)
        else:
            # The directory will already have been added for an index
            src = join(dirname(filename), entry)
        if not os.path.isfile(src):
            out(('File "%s" referenced by file keyword missing.' %
                entry), WARN)
            return
        #
        target_file_name = url2pathname(target)
        targetfile = join(self.target, self.dir, target_file_name)
        dest = join(dirname(targetfile), split(entry)[1])
        comparefile = join(self.compare, self.dir, target_file_name)
        cmp = join(dirname(comparefile), split(entry)[1])
        if comparefiles(src, cmp):
            out('File "%s" identical, skipping.' % entry, INFO)
            return
        if not isdir(dirname(dest)):
            os.makedirs(dirname(dest))
        out('Copying "%s".' % entry, ACTION)
        copy2(src, dest)


    def copy_filemask(self, filemasks, nofiles, filename, target, index=False):
        # below needs testing thoroughly :-)
        if not index:
            srcdir = join(self.dir, dirname(filename))
        else:
            srcdir = dirname(filename)
        #
        target_file_name = url2pathname(target)
        targetfile = join(self.target, self.dir, target_file_name)
        target_dir = dirname(targetfile)
        #
        nofiles = [os.path.abspath(os.path.join(srcdir, os.path.expanduser(pathName))) for pathName in nofiles]
        for mask in filemasks:
            mask = os.path.abspath(os.path.join(srcdir, os.path.expanduser(mask)))
            files = [entry for entry in glob.glob(mask) if entry not in nofiles]
            #
            for entry in files:
                dest = join(target_dir, split(entry)[1])
                comparefile = join(self.compare, self.dir, target_file_name)
                cmp = join(dirname(comparefile), split(entry)[1])
                if comparefiles(src, cmp):
                    out('File "%s" identical, skipping.' % entry, INFO)
                else:
                    if not isdir(dirname(dest)):
                        os.makedirs(dirname(dest))
                    out('Copying "%s".' % entry, ACTION)
                    copy2(src, dest)


    def pruned(self, dir_list):
        if not dir_list:
            # Skip empty directories
            return True
        if '__prune__' in dir_list:
            # Pruned directories
            return True
        return False


    def skipentry(self, entry):
        if entry in ['.svn', '.bzr', '.git', '.hg']:
            return None
        path = join(self.dir, entry)
        if isdir(path):
            dir_list = os.listdir(path)
            if self.pruned(dir_list):
                return None
        return path


    def walk(self):
        """
        Walk the directory tree from the start directory.
        And build the site as we go.
        """
        #
        # The macro file needs to be located *before* we change directory
        # (it might be a relative path)
        self.setmacros(self.macrofile)
        #
        # we'll move to 'start_directory'
        # all future URLs will be relative to this
        old_dir = abspath(os.getcwd())
        os.chdir(self.start)
        #
        # start in the 'root' directory
        # (We treat directories as lists, making it easier
        # to go up and down the tree, turning it into
        # a file path or a URL path as we go - so the root directory
        # is represented as an empty list)
        dir_stack = [ [] ]
        out('Starting in "%s" directory.' % self.start, INFO)
        #
        # we walk the directory tree - processing a directory at a time
        count = 0
        toplevel = True
        while dir_stack:
            self.changed = False
            out('', INFO)
            # next directory to do
            self.dir_as_list = dir_stack.pop()
            #
            # a file path - relative to root directory
            self.dir = os.sep.join(self.dir_as_list)
            #
            # a url path using '/', ending with '/'
            self.dir_as_url = tslash('/'.join(self.dir_as_list))
            #
            out('Processing "%s" directory.' % (self.dir or 'root'), INFO)
            #
            # details from every page that will appear in the index
            self.this_section = []
            # contents of this directory
            dir_list = os.listdir(self.dir or os.curdir)
            if self.pruned(dir_list):
                continue
            if self.skip_html and not self.dir:
                dir_list = [entry for entry in dir_list if not entry.lower() == 'html']
            #
            if ('index.txt' not in dir_list) and not self.force:
                # handle directories that we don't process
                # subdirectories are added to the dir_stack
                dir_stack += self.emptydir(dir_list)
                continue
            #
            # set the default values for this directory
            # these can be set in the restindex of the index page.
            # remove the index page from the list
            # (the index page *might* not be 'index.txt')
            # In the process it retrieves a lot of the info about the
            # index page.
            # FIXME: If an index file has no restindex - this call bombs out
            #       should it be a warning instead ?
            errorcheck = self.execute_safely(self.setdefaults, dir_list, toplevel)
            if errorcheck == False:
                self.output_error('Error in processing index details of directory: "%s"' % self.dir)
                continue
            #
            # if restindex.txt exists it has special meaning
            # it is a series of restindexes for pages
            # we're not building, but are including in the indexes
            if 'restindex.txt' in dir_list:
                dir_list.remove('restindex.txt')
                thisentry = join(self.dir, 'restindex.txt')
                out('Reading "%s".' % thisentry, INFO)
                thefile = open(thisentry).read()
                while thefile:
                    # read the top restindex
                    def ProcessNextRestindex(thefile):
                        restindex, thefile = read_restindex(thefile.split('\n'))
                        if restindex is None:
                            return None
                        #
                        # we never build from 'restindex.txt'
                        restindex['build'] = 'no'
                        data = self.process(restindex, '', 'restindex.txt')
                        self.this_section.append(data)
                        return thefile
                    #
                    thefile = self.execute_safely(ProcessNextRestindex, thefile)
                    if thefile == False:
                        self.output_error('Error in processing the file: "%s"' % thisentry)
                        break
                    if thefile is None:
                        break
                #
                count += 1
            #
            # process every file in this directory
            for entry in dir_list:
                thisentry = self.skipentry(entry)
                if thisentry is None:
                    continue
                subdir = False
                # we only process files that end with '.txt'
                if isfile(thisentry) and not entry.endswith('.txt'):
                    # FIXME: allow '.rst' files ?
                    continue
                elif not isfile(thisentry) and not isdir(thisentry):
                    # can this happen ?
                    # not on windows !
                    continue
                elif isdir(thisentry):
                    # creates a *new* list and adds it to dir_stack
                    dir_stack.append(self.dir_as_list + [entry])
                    #
                    # we only need to process subdirs with an 'index.txt'
                    # to include them in the index if needed
                    thisentry = join(thisentry, 'index.txt')
                    if not isfile(thisentry) and not self.force:
                        continue
                    else:
                        subdir = True
                        entry = join(entry, 'index.txt')
                else:
                    # we only add to the count the *files* in
                    # the directory
                    count += 1
                #
                out('Reading "%s".' % thisentry, INFO)
                #
                def ProcessFile():
                    try:
                        restindex, content, filename = self.get_real_restindex(
                                                        entry, subdir=subdir)
                    except NoRestIndex:
                        # there is nothing to process
                        return True
                    else:
                        data = self.process(restindex, content, filename,
                                                subdir=subdir)
                        # add this page to the current section
                        self.this_section.append(data)
                        return True
                #
                errorcheck = self.execute_safely(ProcessFile)
                if errorcheck == False:
                    self.output_error('Error in processing the file: "%s"' % thisentry)
                    continue
            #
            out('Processing indexfile.', INFO)
            # build the index page with details from ``setdefaults``
            count += 1
            toplevel = False
            #
            errorcheck = self.execute_safely(self.processindex)
            if errorcheck == False:
                self.output_error('Error in processing the index file for directory: "%s"' % self.dir)
                continue
            # then build the pages
            #
            errorcheck = self.execute_safely(self.buildsection)
            if errorcheck == False:
                self.output_error('Error whilst building pages for directory: "%s"' % self.dir)
                continue
        #
        # restore previous directory
        os.chdir(old_dir)
        return count

    def emptydir(self, dir_list):
        """
        If a directory has no "index.txt" there are certain things to be
        taken care of - so that subdirectories can find the right crumb
        for example.

        Returns any sub-directories which should be scanned.

        This sets appropriate values in :
            templatedict
            outputencoding
            crumbdict
            indextree
        """
        dir_stack = []
        # we don't need to do this directory - FIXME: case issues?
        # but we need to make sure all the subdirectories get scanned
        # FIXME: do we really want to recurse into subdirectories ?
        for entry in dir_list:
            path = self.skipentry(entry)
            if path is None:
                continue
            if isdir(path):
                # We want to add any subdirectories to the stack
                # creates a *new* list and adds it to dir_stack
                dir_stack.append(self.dir_as_list + [entry])
        #
        if not self.dir:
            # if 'template.txt' doesn't exist it is handled elsewhere
            self.templatedict[self.dir] = (
                abspath('template.txt'), None)
            self.outputencoding[self.dir] = 'None'
        else:
            self.templatedict[self.dir] = self.templatedict[
                dirname(self.dir)]
            self.outputencoding[self.dir] = self.outputencoding[
                dirname(self.dir)]
        # no crumb for the current directory
        self.crumbdict[self.dir] = None
        self.indextree[self.dir] = None
        #
        return dir_stack


    def provide_default_index(self, filename=None):
        """Provide defaults for a missing index page."""
        if filename is None:
            page_title = split(self.dir.rstrip('/\\'))[1]
        else:
            page_title = splitext(split(filename)[1])[0].replace('_', ' ').title()
        content = self._default_index
        restindex = {
            'page-title': 'Index for %s' % (page_title
                or self._top_level_name),
            'format': 'rest'
            }
        return restindex, content


    def setdefaults(self, thelist, toplevel):
        """
        Set the default values for this directory.

        This reads default values from 'index.txt'.
        *Some* of these may be used for other entries in the directory.
        (For example members of 'default_keywords', the 'crumb', the template
        used for this directory, etc)

        This method is called once per directory, before any of the files
        are processed.

        It does the following things:
            remove 'index.txt' *and* the real index file from ``thelist``
            read the restindex from the index file
            set the relevant default values for the directory
            set the crumb values for the directory (which will be the same
                for every file in the directory)
            set the default template for this directory
            set the default output encoding for this directory
            returns the information it has obtained about the index page:
                (index_page, indexfile, restindex, content, target,
                encoding, final_encoding)

        Because we resolve crumbs here we save them as unicode.
        This means we have to detect encoding of the index page.
        """
        # first we must get the appropriate restindex
        # this means finding the right index file
        indexfile = join(self.dir, 'index.txt')
        if 'index.txt' in thelist:
            thelist.remove('index.txt')
            restindex, content = read_restindex(open(indexfile))
        else:
            # FIXME - provide defaults
            restindex, content = self.provide_default_index()
        # FIXME: validate the returned restindex for sanity ?
        if restindex is None:
            if self.force:
                restindex, _ = self.provide_default_index()
            else:
                # FIXME: Should this be a warning ? (Probably is a fatal error.)
                raise rest2webError('index file has no restindex !')
        #
        # the restindex may specify an alternative file as the index file
        index_page = restindex.get('index-file', 'index.txt')
        if index_page != 'index.txt':
            # it *might* not be in this directory (usually will be though)
            if index_page in thelist:
                # FIXME: what if they use some syntax like './filename' ?
                thelist.remove(index_page)
            # turn the unix relative path into a native path
            indexfile = join(self.dir, url2pathname(index_page))
            # the real restindex for this directory
            # FIXME: trap potential IOError here ?
            restindex, content = read_restindex(open(indexfile))
            if restindex is None:
                if self.force:
                    restindex, _ = self.provide_default_index(indexfile)
                else:
                    # FIXME: Should this be a warning ? (Probably is a fatal error.)
                    raise rest2webError('index file has no restindex !')
        #
        # retrieve any uservalues from after the restindex
        uservalues, content = parse_user_values(
                content.split('\n'), dirname(indexfile))
        uservalues = uservalues or {}
        #
        # indexfile is absolute file path
        # index_page is relative location in unix/url format
        native_index_dir = dirname(indexfile)
        #
        # set some default values for the whole directory
        for entry in default_keywords:
            # if the index page sets a default
            # otherwise use the one from default_restindex
            self.defaults[entry] = restindex.get(
                entry, default_restindex[entry])
        #
        # Next we must find the template for this directory
        # this will be relative to index_dir
        # (if it is specified in the index file)
        # FIXME: seeing as we are reading the template file - we could cache it
        if toplevel and self.override_template:
            # NOTE: Override first template if specified at the command line
            template = self.override_template
        else:
            template = restindex.get('template')
        if template:
            # a template was specified
            temp_filename = join(native_index_dir, template)
            template_encoding = restindex.get('template-encoding')
            if not isfile(temp_filename):
                # template file specified but not found
                raise IOError('Template file - "%s" not found.' % temp_filename)
            if not template_encoding:
                template_encoding = guess_encoding(
                    open(temp_filename).read())[1]
        else:
            # no template file specified
            # try 'template.txt' in this directory first
            temp_filename = join(self.dir, 'template.txt')
            if self.force and not isfile(temp_filename):
                if not dirname(self.dir) in self.templatedict:
                    temp_filename = self._default_template
            if not isfile(temp_filename) and self.dir:
                # 'template.txt' doesn't exist
                # we'll use the template file
                # used by the directory above
                (temp_filename, template_encoding) = self.templatedict[
                    dirname(self.dir)]
                if template_encoding is None:
                    template_encoding = guess_encoding(
                        open(temp_filename).read())[1]
                    if not isfile(temp_filename):
                        # XXXX is this possible ?
                        # (possibly if we don't build anything in the root
                        # directory and a placeholder is inserted by
                        # ``emptydir``)
                        raise IOError('No template file found.')
                    self.templatedict[dirname(self.dir)] = (
                        temp_filename, template_encoding)
            elif not isfile(temp_filename):
                # this is the root directory
                # and no 'template.txt'
                raise IOError('No template file found.')
            else:
                # specified template file exists
                template_encoding = restindex.get('template-encoding')
                if not template_encoding:
                    template_encoding = guess_encoding(
                        open(temp_filename).read())[1]
        #
        # set the template file we finally used for this directory
        # which will be the default for other pages in this directory
        # and subdirectories
        self.templatedict[self.dir] = (
            abspath(temp_filename), template_encoding)
        #
        # the path to the file we're trying to build
        # will be relative to the index file
        target = restindex.get('target')
        #
        # if one isn't specified then we autocreate the name
        # using the 'file-extension' value from the restindex
        if not target:
            fileext = (self.defaults['file-extension'] or
                default_restindex['file-extension'])
            if not fileext.startswith('.'):
                fileext = '.' + fileext
            filename = posixsplit(index_page)[1]
            target_filename = splitext(filename)[0] + fileext
            # handle case when we have an index_page in another directory
            target = pathjoin(index_page, target_filename)
        else:
            target = pathjoin(index_page, target) # web location
        #
        # detect the encoding, so that we can find the crumb
        # and decode to unicode
        self.guessed = False
        encoding = restindex.get('encoding')
        if not encoding:
            encoding = guess_encoding(content)[1]
            self.guessed = True
        #
        # FIXME: uservalues from the page currently override the globals
        #   is this the right way round ?
        global_uservals = enc_uni_dict(self.uservalues, encoding)
        global_uservals.update(uservalues)
        uservalues = global_uservals
        #
        # Plugins
        # XXXX should deal with encoding
        # XXXX indexing will need content
        # XXXX also global plugins
        for plugin in restindex.get('plugins', []):
            uservalues.update(self.do_plugin(plugin, indexfile, target,
                                                restindex, uservalues))
        #
        crumblink = pathjoin(self.dir_as_url, target)
        crumb = restindex.get('crumb')
        if not crumb:
            # FIXME: would need to generate the page content (if rest)
            # to get title, which ought to be the default
            def_crumb = splitext(split(target)[1])[0].title()
            crumb = restindex.get('page-title', def_crumb)
        # unicode
        self.crumbdict[self.dir] = (crumblink, crumb.decode(encoding))
        #
        # next generate the breadcrumbs for this directory
        # they will be the same for each file in the directory
        # we step up from the current directory, up to the root directory
        # getting the crumb for each step
        self.breadcrumbs = []
        crumbling = self.dir
        while crumbling:
            thiscrumb = self.crumbdict.get(crumbling)
            if thiscrumb is not None:
                self.breadcrumbs.append(thiscrumb)
            crumbling = dirname(crumbling)
        rootcrumb = self.crumbdict.get('')
        if (rootcrumb is not None) and (rootcrumb not in self.breadcrumbs):
            self.breadcrumbs.append(rootcrumb)
        self.breadcrumbs.reverse()
        #
        # decode uservalues to unicode
        uservalues = uni_dict(uservalues, encoding)
        #
        # set the output encoding for this directory
        out_enc = restindex.get('output-encoding')
        if out_enc is None and self.dir:
            out_enc = self.outputencoding[dirname(self.dir)]
        elif out_enc is None:
            # the default
            out_enc = 'None'
        self.outputencoding[self.dir] = out_enc
        #
        # seeing as we've done all the work - we'll calculate
        # the final_encoding the index will use
        if out_enc.lower() == 'none':
            final_encoding = encoding
        elif out_enc == 'unicode':
            final_encoding = None
        else:
            final_encoding = out_enc
        if final_encoding and final_encoding.lower() == 'utf8':
            final_encoding = 'utf-8'
        #
        self.section_pages = restindex.get('section-pages', {})
        for entry in self.section_pages:
            if entry not in restindex.get('sectionlist', []):
                if entry is None:
                    # don't need to explicitly defien the default section
                    continue
                raise rest2webError('section-pages value defined, that isn\'t'
                                    ' in the sectionlist - "%s"' % entry)
        #
        # having worked all this out, we might as well keep it around
        self.index_page = (index_page, indexfile, restindex, uservalues, content,
            target, encoding, final_encoding)
        return True


    def get_real_restindex(self, filename, subdir=False):
        """
        Get the parsed restindex for a directory.

        This includes following the 'index-file' value for
        a subdirectory we are including in a section.

        Returns: restindex, content, filename
        (or None if there is no restindex)
        """
        filepath = join(self.dir, filename)
        # this raises restindexError
        # a subclass of SyntaxError
        if not isfile(filepath) and self.force and subdir:
            restindex = {
                'page-title': 'Index for %s' % splitext(split(filename)[0])[0]
                }
            content = ''
        else:
            restindex, content = read_restindex(open(filepath))
        if restindex is None:
            # no restindex, no process :-)
            if not self.force or filename == 'template.txt':
                raise NoRestIndex
            else:
                restindex = {}
        # FIXME: validate the returned restindex for sanity
        #
        # filename is either a file only
        # or if ``subdir=True`` is a 'directory/filename' joined using
        # join
        #
        # need to special case ``subdir=True`` in case ``indexfile`` is set!!!
        # index-file value is specified as a relative unix path,
        # relative to self.dir
        if subdir:
            real_index = restindex.get('index-file')
            if real_index:
                thedir = dirname(filename)
                native_real_index = url2pathname(real_index)
                indexfile = join(
                    self.start, self.dir, thedir, native_real_index)
                # the real restindex for this directory
                restindex, content = read_restindex(open(indexfile))
                if restindex is None:
                    restindex, _ = self.provide_default_index(indexfile)
                restindex['build'] = 'no'
                # this is now unix (URL) format
                filename = pathjoin(thedir + '/', real_index)
            else:
                # turn native to url format
                filename = '/'.join(split(filename))
            #
            if not istrue(restindex.get('include', 'yes')):
                # shortcut if it's a subdir and we don't need to include it
                raise NoRestIndex
        #
        return (restindex, content, filename)


    #
    # FIXME: what if build *and* include are set to No ?
    # FIXME: we could short circuit this ? - but it's a dumb set of options !
    def process(self, restindex, content, filename, subdir=False):
        """
        Process a page - ready to be built.
        Return the data structure to add to the current section.

        If the file is an index file from a subdirectory
        then set ``subdir = True``

        Most of the job is building the right values to put in the namespace
        for when rendering the final page, and also the entry in the index.
        A lot of this is dictated by the restindex.

        Some text is saved as unicode. This means that when the details
        of this page are referenced by other pages (i.e. building sidebars)
        they can be converted to the encoding expected by the other page.

        Other text will be stored in the ``final_encoding`` expected by the
        page when it is rendered.
        """
        filepath = join(self.dir, filename)
        name = splitext(filename)[0]
        #
        # fill in any values missing from the restindex
        # but we need to preserve the *original* file-extension
        orig_file_ext = restindex.get('file-extension')
        for entry in self.defaults:
            if not restindex.has_key(entry):
                # use copy to avoid getting references
                restindex[entry] = deepcopy(self.defaults[entry])
        #
        encoding = restindex['encoding']
        if not encoding:
            encoding = guess_encoding(content)[1]
            out('Guessing encoding. We guessed: %s'% encoding, INFO)
        #
        # a relative url path
        target = restindex['target']
        if not target:
            fileext = restindex['file-extension']
            if subdir and not orig_file_ext:
                fileext = default_restindex['file-extension']
            if not fileext.startswith('.'):
                fileext = '.' + fileext
            target = splitext(filename)[0] + fileext
        else:
            target = pathjoin(filename, target)
        #
        pagepath = pathjoin(self.dir_as_url, target)
        #
        (orig_uservalues, content) = parse_user_values(
            content.split('\n'),
            join(self.dir, dirname(filename)))
        orig_uservalues = orig_uservalues or {}
        #
        global_uservals = enc_uni_dict(self.uservalues, encoding)
        global_uservals.update(orig_uservalues)
        orig_uservalues = global_uservals
        #
        # Plugins
        # FIXME: should deal with encoding
        # FIXME: indexing will need content passing to plugin
        if not subdir:
            for plugin in restindex['plugins']:
                orig_uservalues.update(self.do_plugin(plugin, filepath, target,
                                                restindex, orig_uservalues))
            # also copy files (from restindex) into same dir as target
            for entry in restindex['file']:
                self.copy_file(entry, filename, target)
            ##self.copy_filemask(restindex['filemask'], restindex['nofile'], filename, target)
        #
        # FIXME: what about values that are lists/dictionaries ?
        uservalues = uni_dict(orig_uservalues, encoding)
        #
        # build the body of the page
        # even if subdir is True we still build to obtain page title
        # FIXME: can we cache this - wasteful ?
        rest_dict = None
        title = restindex['page-title']
        if title:
            title = unicode(title, encoding)
        # if we have any uservalues
        # render them into content
        # which *may* have come from a different file
        # if the 'body' value was used
        # NOTE: we have to *assume* that the uservalues (and restindex !)
        # NOTE: are the same encoding as the content
        if uservalues and istrue(restindex['build']):
            # both in original encoding, so should be ok ?
            # FIXME: Should we do this for subdir ?
            # NOTE: orig_uservalues not reused, so ok to pollute the dictionary
            #   by rendering in it as a namespace.
            add_modules(orig_uservalues)
            content = render_well(content, orig_uservalues, uservalues=True)
        if restindex['format'] == 'rest':
            # extract title, subtitle
            # FIXME: shouldn't try to build here
            # FIXME: and should provide a better default title
            try:
                doctitle = 1
                if 'page-title' in restindex and not self.promote_headers:
                    doctitle = 0
                entry = html_parts(
                    content, source_path=join(self.dir, filename), input_encoding=encoding,
                    initial_header_level=int(restindex['initialheaderlevel']),
                    doctitle=doctitle)
            except ApplicationError:
                if istrue(restindex['build']):
                    raise
                entry = {
                    'title': '',
                    'html_body': '',
                }
            # FIXME: defaults to '' in the absence of a title
            title = title or strip_tags(entry['title']) or ''
            # extract the body
            body = entry['html_body']
            rest_dict = entry
        else:
            body = unicode(content, encoding)
        #
        # We need the crumb in unicode
        # if we haven't got one - we'll use the title
        crumb = restindex['crumb']
        if not crumb:
            unicrumb = title
        else:
            unicrumb = unicode(crumb, encoding)
        # get the tags
        tags = [unicode(tag, encoding) for tag in restindex['tags']]
        #
        # processed as reST
        page_description = description_rest(
            restindex['page-description'], encoding)
        #
        # We use link title or title or crumb
        # FIXME: is this documented ?
        # could be filename if neither title nor crumb exists
        link_title = (unicode(restindex['link-title'], encoding) or
            title or unicrumb)
        #
        # can be None
        section = restindex['section']
        if section is not None:
            section = unicode(section, encoding)
        #
        # body, title, page_description, link_title, crumb
        # are now unicode strings
        output_encoding = restindex.get(
            'outputencoding', self.outputencoding[self.dir])
        lower_enc = output_encoding.lower()
        final_encoding = None
        if lower_enc == 'none':
            final_encoding = encoding
        elif lower_enc != 'unicode':
            # 'unicode' means leave as unicode
            final_encoding = output_encoding
        if final_encoding.lower() == 'utf8':
            final_encoding = 'utf-8'
        #
        # we now encode the body, title, and crumb as per the choice
        # in the restindex; if final_encoding is None, the encode function
        # leaves it as unicode
        body = encode(body, final_encoding)
        title = encode(title, final_encoding)
        crumb = encode(unicrumb, final_encoding)
        #
        targetfile = join(self.target, self.dir, url2pathname(target))
        file_dict = {
            'source_file': join(os.getcwd(), filepath),
            'current_dir': self.dir,
            'target_dir': join(os.getcwd(), self.target, self.dir),
            'full_page_url': pagepath,
            'target_file': join(os.getcwd(), targetfile),
        }
        namespace = None
        # if we're building the page
        # we need to create the namespace
        if not subdir and istrue(restindex['build']):
            # sort breadcrumbs including encoding appropriately
            # (from the unicode they are stored with)
            breadcrumbs = []
            for crumbpath, crumb_title in self.breadcrumbs:
                crumbpath = relpathto(
                    self.dir_as_url, target, '/' + crumbpath)
                crumb_title = encode(crumb_title, final_encoding)
                breadcrumbs.append((crumbpath, crumb_title))
            # filename rather than full pagepath
            breadcrumbs.append((posixsplit(pagepath)[1], crumb))
            #
            # create the namespace we build the template in
            # title, body, breadcrumbs, indexdata, pagepath, pagename,
            # encoding, anything in namespace becomes directly a variable
            # when rendering the page
            #
            namespace = {}
            namespace['title'] = title
            namespace['breadcrumbs'] = breadcrumbs
            namespace['tags'] = [encode(tag, final_encoding) for tag in tags]
            # not yet !
            #  namespace['sections'] = None
            namespace['pagename'] = split(target)[1]
            # full path
            namespace['pagepath'] = pagepath
            namespace['encoding'] = encoding
            namespace['output_encoding'] = output_encoding
            namespace['final_encoding'] = final_encoding
            # target, relative to index page
            namespace['target'] = target
            namespace['path_to_root'] = relpathto(
                self.dir_as_url, target, '/')
            # a copy rather than a reference! should be [] for a normal page??
            namespace['sectionlist'] = list(restindex['sectionlist'])
            # will be None for a page not in reST format
            namespace['rest_dict'] = rest_dict
            # careful now !
            namespace['Processor'] = self
            namespace['body'] = body
            namespace['modified'] =  os.path.getmtime(filepath)
            namespace['modtime'] = time.ctime(namespace['modified'])
            namespace['modtimeiso'] = datetime.datetime.fromtimestamp(
                namespace['modified']).isoformat()
            namespace['plugins'] = restindex['plugins']
            namespace['page_description'] = encode(page_description,
                                                        final_encoding)
            #
            template = restindex['template']
            if template:
                temp_filename = join(self.dir, template)
                if not isfile(temp_filename):
                    raise IOError('Template file - "%s" not found.' %
                        temp_filename)
                template_encoding = restindex['template-encoding']
                if not template_encoding:
                    template_encoding = guess_encoding(
                        open(temp_filename).read())[1]
            else:
                (temp_filename, template_encoding) = self.templatedict[
                    self.dir]
            namespace['template_file'] = temp_filename
            namespace['template_encoding'] = template_encoding
            namespace.update(file_dict)
        #
        # anything in index is available as a member of the page dictionary
        index = {'target': target }
        index['subdir'] = subdir
        index['section'] = section
        index['link-title'] = link_title
        index['page-description'] = page_description
        index['crumb'] = unicrumb
        index['namespace'] = namespace
        index['build'] = not subdir and istrue(restindex['build'])
        index['include'] = istrue(restindex['include'])
        index['filename'] = filename
        index['index'] = False
        index['uservalues'] = enc_uni_dict(uservalues, final_encoding)
        index['name'] = name
        index['restindex'] = restindex
        index.update(file_dict)
        # 'link-title', 'page-description', 'crumb', and 'section' are all unicode
        # FIXME: should target be ? (unicode filesystems ??)
        #
        return index

    def processindex(self):
        """
        Process the index page for a directory.

        Most of the work has been done by ``setdefaults``,
        so we just need to put the namespace (etc) together.

        This will also establish some data that is going to be made available
        to all the pages in their namespaces, *including* building the
        sections data structure.
        """
        # unpack data from setdefaults
        (index_page, filename, restindex, uservalues, content,
            target, encoding, final_encoding) = self.index_page
        #
        # fill in any values missing from the restindex
        for entry in self.defaults:
            if not restindex.has_key(entry):
                restindex[entry] = deepcopy(self.defaults[entry])
        #
        if self.guessed:
            # we had to guess the encoding, let's admit it
            out('Guessing encoding. We guessed: %s' % encoding, INFO)
        #
        # copy files (from restindex) into same dir as target
        for entry in restindex['file']:
            self.copy_file(entry, filename, target, index=True)
        ##self.copy_filemask(restindex['filemask'], restindex['nofile'], filename, target, index=True)
        #
        # a list of encoded strings becomes a list of unicode strings!
        sectionlist = [sec is None or unicode(sec, encoding)
            for sec in restindex['sectionlist']]
        # this expression swaps None for True
        listswap(sectionlist, True, None)
        #
        # a dictionary of unicode strings
        sectiontitles = uni_dict(restindex['section-title'], encoding)
        # a dictionary of encoded strings!
        sectiondescriptions = restindex['section-description']
        #
        indexes = self.this_section
        def_section = {
            'title': sectiontitles.get(None, ''),
            'description': description_rest(
                sectiondescriptions.get(entry, ''), encoding),
            'pages': [],
            'section-pages': []
        }
        indextree_sections = {
            None: (def_section['title'], def_section['description'])}
        # None is default section - means you don't *need* to use sections
        # everything with no section specified will go into sections[None]
        self.sections = {None: def_section }
        #
        # might be None
        for entry in sectionlist:
            self.sections[entry] = {}
            if entry is None:
                entry_title = ''
            else:
                entry_title = entry.title()
            self.sections[entry]['title'] = sectiontitles.get(entry,
                                                                entry_title)
            # process as reST
            self.sections[entry]['description'] = description_rest(
                sectiondescriptions.get(entry, ''), encoding)
            self.sections[entry]['pages'] = []
            indextree_sections[entry] = (
                self.sections[entry]['title'],
                self.sections[entry]['description'])
        #
        for page in indexes:
            if not page['include']:
                # the page is not passed in 'sections'
                continue
            section = page['section']
            try:
                self.sections[section]['pages'].append(page)
            except KeyError:
                raise KeyError('Page "%s" claims to be in section "%s",'
                    ' which doesn\'t exist.' % (page['filename'], section))
        #
        # sections is now a dictionary with an entry per section
        # (including the default section - keyed by None)
        # each section dictionary has:
        #   unicode section title and unicode section description (or '')
        #   a list of all the pages in each each section
        #   where each page is the entry returned by ``process``
        #
        # next make sure that the pages in each section are ordered as
        # per 'section-pages' (if specified)
        self.order_pages(self.sections)
        #
        namespace = None
        crumb = restindex['crumb']
        # establish a default crumb if all else fails
        unicrumb = u''
        if crumb:
            unicrumb = unicode(crumb, encoding)
        page_description = description_rest(
            restindex['page-description'], encoding)   # processed as reST
        link_title = unicode(restindex['link-title'], encoding)
        #
        title = restindex['page-title']
        if title:
            title = unicode(restindex['page-title'], encoding)
        #
        # can be None
        section = restindex['section']
        if section is not None:
            section = unicode(section, encoding)
        #
        targetfile = join(self.target, self.dir, url2pathname(target))
        file_dict = {
            'source_file': join(os.getcwd(), join(self.dir, url2pathname(index_page))),
            'current_dir': self.dir,
            'target_dir': join(os.getcwd(), self.target, self.dir),
            'full_page_url': '/' + pathjoin(self.dir_as_url, target),
            'target_file': join(os.getcwd(), targetfile),
        }
        if istrue(restindex['build']):
            # build the body of the page
            rest_dict = None
            # if we have any uservalues
            # render them into content
            # FIXME: we have to *assume* that the uservalues
            # FIXME: are the same encoding as the content
            if uservalues:
                # need to re-encode uservalues
                # NOTE: orig_uservalues not reused, so ok to pollute the
                #   dictionary by rendering in it as a namespace.
                orig_uservalues = enc_uni_dict(uservalues, encoding)
                add_modules(orig_uservalues)
                content = render_well(content, orig_uservalues,
                    uservalues=True)
            if restindex['format'] == 'rest':
                # extract title, subtitle
                doctitle = 1
                if 'page-title' in restindex and not self.promote_headers:
                    doctitle = 0
                entry = html_parts(content, source_path = filename,
                    input_encoding = encoding, initial_header_level=int(restindex['initialheaderlevel']),
                    doctitle=doctitle)
                # FIXME: defaults to '' in the absence of a title
                title = title or strip_tags(entry['title']) or ''
                # extract the body
                body = entry['html_body']
                rest_dict = entry
            else:
                body = unicode(content, encoding)
            #
            if not crumb:
                unicrumb = title
            #
            # FIXME: is this documented? Could be filename if neither title
            # nor crumb exists
            link_title = link_title or title or unicrumb
            #
            # we now encode the body, title, and crumb as per the choice
            # in the restindex
            body = encode(body, final_encoding)
            title = encode(title, final_encoding)
            #
            pagepath = pathjoin(self.dir_as_url, target)
            breadcrumbs = []
            for crumbpath, crumb_title in self.breadcrumbs:
                crumbpath = relpathto(
                    self.dir_as_url, target, '/' + crumbpath)
                crumb_title = encode(crumb_title, final_encoding)
                breadcrumbs.append((crumbpath, crumb_title))
            # the previously created crumb *might* be wrong...
            # (because we didn't render content to get the title)
            # correcting it here is *inconsistent* of course
##            breadcrumbs[-1] = (pagepath, crumb)
            #
            # create the namespace we build the template in
            # title, body, breadcrumbs, indexdata, pagepath, pagename,
            # encoding, anything in namespace becomes directly a variable
            #
            namespace = {}
            namespace['title'] = title
            namespace['breadcrumbs'] = breadcrumbs
            namespace['tags'] = [encode(unicode(tag, encoding), final_encoding)
                                        for tag in restindex['tags']]
            namespace['pagename'] = split(target)[1]
            namespace['pagepath'] = pagepath
            namespace['encoding'] = encoding
            namespace['output_encoding'] = self.outputencoding[self.dir]
            namespace['final_encoding'] = final_encoding
            namespace['path_to_root'] = relpathto(
                self.dir_as_url, target, '/')
            namespace['rest_dict'] = rest_dict
            # careful now! :-)
            namespace['Processor'] = self
            namespace['body'] = body
            try:
                namespace['modified'] = os.path.getmtime(filename)
            except (IOError, OSError):
                # happens when creating a default index
                namespace['modified'] = time.time()
            namespace['modtimeiso'] = datetime.datetime.fromtimestamp(
                namespace['modified']).isoformat()
            namespace['modtime'] = time.ctime(namespace['modified'])
            namespace['plugins'] = restindex['plugins']
            namespace['page_description'] = encode(page_description,
                                                            final_encoding)
            #
            # for an index - template is always worked out in getdefaults
            temp_filename, template_encoding = self.templatedict[self.dir]
            namespace['template_file'] = temp_filename
            namespace['template_encoding'] = template_encoding
            namespace['_dir_as_url'] = self.dir_as_url
            namespace.update(file_dict)
        else:
            link_title = link_title or title or unicrumb
        #
        the_index_page = {
            'target': target,
            # unicode :-)
           'crumb': self.crumbdict[self.dir][1],
           'namespace': namespace,
           'link-title': link_title,
           'section': section,
           'subdir': False,
           'page-description': page_description,
           'filename': filename,
           'name': splitext(filename)[0],
           'include': istrue(restindex['include']),
           'index': True,
           'uservalues': enc_uni_dict(uservalues, final_encoding),
           'restindex': restindex,
        }
        the_index_page.update(file_dict)
        # XXXX a magic section ??
        self.sections['__index__'] = {
            'title': '',
            'description': '',
            'pages': [the_index_page],
        }
        #
        # add the index page to the current section
        indexes.append(the_index_page)
        # add the whole directory to the indextree structure
        # addtree has to properly preserve encodings and relative URLs
        self.addtree(indexes, indextree_sections, sectionlist)
        self.sectionlist = sectionlist

    def buildsection(self):
        """
        Actually build and save the pages for the current directory.

        This means put the content into the templates, including processing
        any embedded code.

        It must handle all the relative locations and different encodings
        properly. (Particularly for the indextree data structure).
        """
        #
        # when building each page,
        # get the template filename from the namespace
        # insert sections into the namespace
        # render the body
        # deal with macros
        #
        for page in self.this_section:
            if page['namespace'] is None:
                # not building
                continue
            #
            namespace = page['namespace']
            target = page['target']
            #
            temp_filename = namespace['template_file']
            template_encoding = namespace['template_encoding']
            final_encoding = namespace['final_encoding']
            #
            # get the template
            if not temp_filename in self._template_files:
                temp_file = open(temp_filename).read()
                self._template_files[temp_filename] = temp_file
            else:
                temp_file = self._template_files[temp_filename]
            #
            # decode
            temp_file = unicode(temp_file, template_encoding)
            # encode
            temp_file = encode(temp_file, final_encoding)
            #
            filename = namespace['pagepath']
            #
            the_sections = handle_sections(
                self.sections, final_encoding, self.dir_as_url, target)
            #
            # FIXME: hack - retrieve the indexpage and remove it
            # from the_sections
            __index__ = the_sections['__index__']['pages'][0]
            del the_sections['__index__']
            #
            namespace['sections'] = SectionDict(the_sections.items())
            namespace['default_section'] = namespace['sections'][None]
            namespace['indexpage'] = __index__
            namespace['sectionlist'] = [encode(mem, final_encoding)
                                                for mem in self.sectionlist]
            #
            # set the key order of the 'sections' dictionary
            # This assumes that the sectionlist from the restindex is
            # either complete or empty.
            # FIXME: hack - add the default section
            if None not in namespace['sectionlist']:
                if not the_sections[None]['pages']:
                    # if there are no pages in the default section
                    del namespace['sections'][None]
                else:
                    namespace['sectionlist'].append(None)
            namespace['sections'].setkeys(namespace['sectionlist'] or
                namespace['sections'].keys())
            #
            indextree, thispage = self.buildtree(page, final_encoding)
            namespace['indextree'] = indextree
            namespace['thispage'] = thispage
            #
            target_file_name = url2pathname(target)
            targetfile = join(self.target, self.dir, target_file_name)
            out('Building %s' % filename, INFO)
            #
            # add the functions and uservalues
            for entry in functions.__all__:
                namespace[entry] = getattr(functions, entry)
            uservalues = page['uservalues']
            namespace.update(uservalues)
            #
            functions._set_uservalues(namespace, uservalues)
            #
            # render macros
            if self.macrodir is not None:
                cur_dir = os.getcwd()
                # change directory to the directory of the macros file
                os.chdir(self.macrodir)
            try:
                self.macros['set_uservalues'](namespace, uservalues)
            except KeyError:
                pass
            namespace['body'] = textmacros.replace_all(
                                    namespace['body'], self.macros, 1)
            if self.macrodir is not None:
                os.chdir(cur_dir)
            #
            if self.debug:
                # DEBUG mode
                def exit():
                    sys.exit()
                namespace['exit'] = exit
                namespace['local_vars'] = locals()
                namespace['self'] = self
                namespace['temp_file'] = temp_file
                interactive(namespace)
            add_modules(namespace)
            thepage = render_well(temp_file, namespace, final_encoding=final_encoding)
            #
            if self.typogrify and page['restindex']['typogrify']:
                thepage = typogrify.filters.typogrify(thepage)
            #
            # if final_encoding was ``None`` thepage is now unicode
            # so we need to re-encode
            if type(thepage) is unicode:
                thepage = thepage.encode(template_encoding)
            # FIXME: why template_encoding ? (can't leave it as unicode though)
            #
            targetdir = dirname(targetfile)
            if not isdir(targetdir):
                out('Creating Directory : %s' % targetdir, ACTION)
                os.makedirs(targetdir)
            #
            # compare
            compfile = join(self.compare, self.dir, target_file_name)
            same = False
            if isfile(compfile):
                # True or False
                same = (thepage == open(compfile, 'r').read())
            if same is False:
                out('Writing %s' % target, ACTION)
                open(targetfile, 'w').write(thepage)
            else:
                out('Skipping "%s". Identical file exists.' % target, INFO)

    def addtree(self, indexes, sections, sectionlist):
        """Add the indextree entry for the current directory."""
        secs = {}
        this_sect = {}
        for page in indexes:
            if not page['include'] and not page['index']:
                # FIXME: what if we don't 'include' the index page?
                # FIXME: possible I guess?
                continue
            #
            newpage = { }
            newpage['subdir'] = page['subdir']
            # absolute path to this file
            newpage['target'] = pathjoin(self.dir_as_url, page['target'])
            newpage['section'] = page['section']
            newpage['link-title'] = page['link-title']
            newpage['crumb'] = page['crumb']
            newpage['page-description'] = page['page-description']
            newpage['name'] = page['name']
            # FIXME: Warning, encoding isn't handled
            for entry in ('restindex', 'uservalues', 'source_file', 'current_dir', 'target_dir',
                          'full_page_url', 'target_file'):
                newpage[entry] = page[entry]
            #
            if not page['index']:
                if secs.has_key(page['section']):
                    secs[page['section']].append(newpage)
                else:
                    secs[page['section']] = [newpage]
            else:
                this_sect.update(newpage)
        # Order of pages in this list should follow
        # sectionlist and section-pages
        pages = []
        for sec in sectionlist or [None]:
            section = secs.get(sec, [])
            if sec in self.section_pages:
                sec_list = self.section_pages[sec]
                these_pages = {}
                for page in section:
                    these_pages[page['name']] = page
                for entry in sec_list:
                    pages.append(these_pages.pop(entry))
                pages += these_pages.values()
            else:
                pages += section
        #
        this_sect['pages'] = pages
        this_sect['sections'] = sections
        this_sect['sectionlist'] = sectionlist
        this_sect['dir_as_url'] = self.dir_as_url
        #
        # this_sect now represents the index page for this
        self.indextree[self.dir] = this_sect

    def buildtree(self, cur_page, encoding):
        """
        Given the current page return the indextree structure and thispage
        pointer.
        """
        # abs location of cur_page
        cur_loc = pathjoin(self.dir_as_url, cur_page['target'])
        #
        branches = []
        thedir = self.dir
        while thedir:
            this_index = self.indextree[thedir]
            if this_index is not None:
                branches.insert(0, this_index)
            thedir = dirname(thedir)
        branchroot = self.indextree.get('')
        if branchroot is not None and branchroot not in branches:
            branches.insert(0, branchroot)
        #
        newlist = []
        i = -1
        # start at top level, work our way down the tree
        while i < len(branches) - 1:
            i += 1
            branch = branches[i]
            # handle the basics
            this_sect = sort_page(branch, encoding)
            this_sect['subdir'] = branch['subdir']
            # relative path to this file
            this_sect['target'] = relpathto(
                self.dir_as_url, cur_loc, branch['target'])
            this_sect['thispage'] = False
            #
            sectionlist = this_sect['sectionlist'] = [encode(mem, encoding)
                for mem in branch['sectionlist']]
            sections = {}
            for entry in branch['sections']:
                title, desc = branch['sections'][entry]
                sections[encode(entry, encoding)] = (
                    encode(title, encoding), encode(desc, encoding))
            this_sect['sections'] = sections
            #
            pages = []
            for page in branch['pages']:
                newpage = sort_page(page, encoding)
                newpage['subdir'] = page['subdir']
                newpage['sectionlist'] = sectionlist
                newpage['sections'] = sections
                newpage['parent'] = this_sect
                # relative path to this file
                newpage['target'] = relpathto(
                    self.dir_as_url, cur_loc, page['target'])
                newpage['thispage'] = False
                if not newpage['subdir']:
                    newpage['pages'] = None
                else:
                    newpage['pages'] = []
                pages.append(newpage)
            this_sect['pages'] = pages
            #
            if i > 0:
                thepages = branches[i-1]['pages']
                if not thepages:
                    # either None or [] - parent directory claims
                    # to have no pages
                    # FIXME: Should this be INFO or WARN ?
                    out('No pages in parent section.', INFO)
                    newlist[i-1]['pages'] = [this_sect]
                else:
                    for num in range(len(thepages)):
                        if thepages[num]['target'] == branch['target']:
                            del newlist[i-1]['pages'][num]
                            newlist[i-1]['pages'].insert(num, this_sect)
                            break
                    else:
                        newlist[i-1]['pages'].append(this_sect)
                this_sect['parent'] = newlist[i-1]
            else:
                this_sect['parent'] = None
            #
            newlist.append(this_sect)
        #
        for page in newlist[-1]['pages']:
            if split(cur_page['target'])[1] == page['target']:
                thispage = page
                page['thispage'] = True
                break
        else:
            # for index pages
            if split(cur_page['target'])[1] == newlist[-1]['target']:
                thispage = newlist[-1]
                newlist[-1]['thispage'] = True
            else:
                # for pages that have ``include: no``
                thispage = None
        return newlist[0], thispage

    def do_plugin(self, plugin, filename, target, restindex, uservalues):
        """Run a plugin - first checking we can/have loaded it."""
        if not plugin in self.plugins:
            try:
                p = __import__('rest2web.plugins', globals(),
                                locals(), [plugin])
                p = getattr(p, plugin)
            except (ImportError, AttributeError):
                raise ImportError('Plugin "%s" doesn\'t exist or has no'
                                                    ' Plugin class' % plugin)
            self.plugins[plugin] = p.Plugin(self)
        return self.plugins[plugin].page(filename, target, restindex, uservalues)

    def order_pages(self, sections):
        """
        Order the pages in each section as 'section-pages' (if specified).

        Additionally, create a list of all the pages in order.
        """
        self.page_index = []
        for sec in self.section_pages:
            section = sections[sec]
            sec_list = self.section_pages[sec]
            pages = {}
            for page in section['pages']:
                pages[page['name']] = page
            section['pages'] = []
            for entry in sec_list:
                try:
                    p = pages.pop(entry)
                except KeyError:
                    sec = sec or 'Default Section'
                    raise rest2webError('Page specified in "section-pages" '
                                        'that doesn\'t exist. Section "%s", '
                                        'page "%s"' % (sec, entry))
                else:
                    section['pages'].append(p)
                    self.page_index.append(p)
            remaining = pages.values()
            section['pages'] += remaining
            self.page_index += remaining

def sort_page(inpage, encoding):
    """
    A specialised function for ``buildtree`` that encodes specific members
    of page dictionaries
    """
    outpage = {}
    entries = ['section', 'link-title', 'crumb', 'page-description']
    for entry in entries:
        outpage[entry] = encode(inpage[entry], encoding)
    # FIXME: Warning, encoding isn't handled
    for entry in ('restindex', 'uservalues', 'source_file', 'current_dir', 'target_dir',
                  'full_page_url', 'target_file'):
        outpage[entry] = inpage[entry]
    return outpage

def handle_sections(sections, encoding, cur_loc, target):
    """
    Given a 'sections' datastructure appropriately encode.

    The 'sections' data structure is a dictionary of dictionaries.
    All the members are unicode strings, or lists of unicode strings... etc.

    This function returns a new data structure
    with all the unicode turned to encoded strings. (unless encoding is None)

    This *also* handles making the targets to all of the pages relative
    to the right location.
    """
    # FIXME: could this use sort_page as well?
    out_dict = {}
    for entry in sections:
        if entry is not None:
            # could do try..except here... ?
            enc_entry = encode(entry, encoding)
        else:
            enc_entry = None
        this_sect = sections[entry]
        new_sect = {}
        new_sect['title'] = encode(this_sect['title'], encoding)
        new_sect['description'] = encode(this_sect['description'], encoding)
        new_sect['pages'] = []
        thepages = this_sect['pages']
        for page in thepages:
            newpage = {}
            # sort out relativity
            newpage['target'] = relpathto(cur_loc, target, page['target'])
            newpage['section'] = enc_entry
            newpage['link-title'] = encode(page['link-title'], encoding)
            newpage['page-description'] = encode(
                page['page-description'], encoding)
            newpage['crumb'] = encode(page['crumb'], encoding)
            # no conversion - just a reference
            newpage['namespace'] = page['namespace']
            newpage['subdir'] = page['subdir']
            # FIXME: Warning, encoding isn't handled
            for entry in ('restindex', 'uservalues', 'source_file', 'current_dir', 'target_dir',
                          'full_page_url', 'target_file'):
                newpage[entry] = page[entry]
            new_sect['pages'].append(newpage)
        out_dict[enc_entry] = new_sect
    return out_dict
