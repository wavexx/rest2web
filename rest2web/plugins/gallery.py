# Subversion Details
# $LastChangedDate: 2005-06-21 09:07:43 +0100 (Tue, 21 Jun 2005) $
# $LastChangedBy: fuzzyman $
# $HeadURL: https://svn.rest2web.python-hosting.com/trunk/rest2web/restindex.py $
# $LastChangedRevision: 36 $

# The plugin that generates static gallery pages.
# http://www.voidspace.org.uk/python/rest2web

# Copyright Michael Foord, 2005.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# For information about bugfixes, updates and support, please join the
# rest2web mailing list.
# https://lists.sourceforge.net/lists/listinfo/rest2web-develop
# Comments, suggestions and bug reports welcome.
# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# E-mail fuzzyman@voidspace.org.uk

"""
Build a single html gallery page from a directory of images.
It generates a single index page, and saves individual html
files for each image.

Requires PIL, pythonutils, and rest2web to be installed
"""

import os
from posixpath import join as posixjoin
from copy import deepcopy
from configobj import ConfigObj

from rest2web.pythonutils.urlpath import relpathto, pathjoin
from rest2web.restutils import replace

# image imports
try:
    from PIL import Image
except ImportError:
    raise ImportError('Importing PIL - Python Imaging Library - failed.')

image_types = ('.bmp', '.png', '.gif', '.ico', '.jpg', '.ecw', '.emf', '.fsh',
    '.jpm', '.ldf', '.lwf', '.pcx', '.pbm', '.pgm', '.ppm', '.raw', '.tga',
    '.tif')


class Plugin(object):
    def __init__(self, processor):
        self.processor = processor
        # XXXX global plugins will probably need access
        # XXXX to the initital config file here

    def page(self, filepath, target, restindex, uservalues):
        param_list = ['thumb_size', 'gallery_dir', 'gallery_url',
                    'data_file', 'page_template', 'entry_template',
                    'gallery_mode']
        for entry in param_list:
            if entry not in uservalues:
                raise ValueError, ('Missing value required by Gallery - "%s"'
                                        % entry)
        # make uservalues a copy, *not* a reference
        params = deepcopy(uservalues)
        params['thumb_size'] = params['thumb_size'].strip().split(',')
        #
        # this is how we know we're coming from the Plugin
        # rather than running standalone
        params['gallery_page'] = None
        #
        # make the values in the uservalues
        # relative to the right place
        params['gallery_dir'] = os.path.join(self.processor.dir,
                                                params['gallery_dir'])
        params['data_file'] = os.path.join(self.processor.dir,
                                                params['data_file'])
        params['page_template'] = os.path.join(self.processor.dir,
                                                params['page_template'])
        params['entry_template'] = os.path.join(self.processor.dir,
                                                params['entry_template'])
        #
        gall_url = posixjoin('/', self.processor.dir_as_url, target)
        html_url = posixjoin(pathjoin(gall_url, params['gallery_url']),
                                                                    'html/')
        params['path_back'] = relpathto('/', html_url, gall_url)
##        print target, gall_url, html_url, params['path_back']
        data = get_info(params)
        #
        return {'gallery': make_pages(params, data)}

def get_info(config):
    """Gets all the data for the gallery and builds thumbnails."""
    # config data
    # x, y
    thumb_size = [int(val) for val in config['thumb_size']]
    gallery_dir = config['gallery_dir']
    thumb_dir = os.path.join(gallery_dir, 'thumbnails')
    thumb_prefix = 'tn_'
    data_file = config['data_file']
    #
    # get the image data file
    # this will create it if it doesn't yet exist
    try:
        # for backwards compatibility with ConfigObj3
        data = ConfigObj(data_file, flatfile=False)
    except TypeError:
        # no such thing as a flatfile in ConfigObj 4
        data = ConfigObj(data_file)
    #
    # if we are in mode 2 then just return the data file
    if config['gallery_mode'] == '2':
        return data
    #
    for image in data.keys():
        # check all the files exist
        if not (os.path.isfile(os.path.join(gallery_dir, image))
                and os.path.splitext(image)[1].lower() in image_types):
            # remove any missing one
            del data[image]
    #
    if not os.path.isdir(thumb_dir):
        os.makedirs(thumb_dir)
    #
    the_list = os.listdir(gallery_dir)
    for image in the_list:
        path = os.path.join(gallery_dir, image)
        if os.path.isdir(path):
            continue
        name, ext = os.path.splitext(image)
        if ext.lower() not in image_types:
            continue
        im = Image.open(path)
        size = im.size
        try:
            this = data[image]
        except KeyError:
            # this image isn't in the file
            data[image] = {}
            this = data[image]
            this['title'] = name.replace('_', ' ').title()
            this['description'] = ''
            this['size'] = size
            this['filesize'] = os.path.getsize(path)
        else:
            # we do have the filename
            # but has the image changed ?
            x = int(this['size'][0])
            y = int(this['size'][1])
            if not (x, y) == size:
                # the image has changed since last time (size is different)
                this['size'] = size
                this['filesize'] = os.path.getsize(path)
        #
        # always regenerate thumb nails
        thumb_name = os.path.join(thumb_dir, thumb_prefix + name + ext)
        im.thumbnail(thumb_size)
        try:
            im.save(thumb_name)
        except IOError:
            # FIXME: This causes us to skip animated jpgs
            del data[image]
        else:
            this['thumb_size'] = im.size
            this['thumbnail'] = thumb_prefix + name + ext
    #
    # save image data
    data.write()
    return data

def make_pages(config, data):
    """Create the html pages for the individual files."""
    # config data
    # x, y
    thumb_size = [int(val) for val in config['thumb_size']]
    gallery_dir = config['gallery_dir']
    thumb_prefix = 'tn_'
    entry = open(config['entry_template']).read()

    page = open(config['page_template']).read()
    gallery_page = config['gallery_page']
    #
    gallery_url = config['gallery_url']
    thumb_url = posixjoin(gallery_url, 'thumbnails')
    html_url = posixjoin(gallery_url, 'html')
    html_dir = os.path.join(gallery_dir, 'html')
    #
    if not os.path.isdir(html_dir):
        os.makedirs(html_dir)
    #
    main_out = []
    i = -1
    image_list = data.keys()
    length = len(image_list)
    right_image = right_name = right_link = right_thumb = ''
    right_thumb_width = right_thumb_height = right_title = ''
    right_description = None
    while i < length:
        i += 1
        if i != 0:
            left_image = image
            left_name = name
            left_link = link
            left_thumb = thumb
            left_thumb_width = thumb_width
            left_thumb_height = thumb_height
            left_title = title
        image = right_image
        name = right_name
        link = right_link
        thumb = right_thumb
        thumb_width = right_thumb_width
        thumb_height = right_thumb_height
        title = right_title
        description = right_description
        #
        if i != length:
            right_name = image_list[i]
            right_image = data[right_name]
            # XXXX how do we create the filename
            # XXXX always a straight '.html' ?
            right_link = os.path.splitext(right_name)[0] + '.html'
            right_thumb = right_image['thumbnail']
            right_thumb_width = str(right_image['thumb_size'][0])
            right_thumb_height = str(right_image['thumb_size'][1])
            right_title = right_image['title']
        #
        if i == 0:
            continue
        #
        width = str(image['size'][0])
        height = str(image['size'][1])
        #
        # generate the entry for the main page
        replace_dict = {}
        replace_dict['**link**'] = posixjoin(html_url, link)
        replace_dict['**thumb**'] = posixjoin(thumb_url, thumb)
        replace_dict['**width**'] = str(thumb_width)
        replace_dict['**height**'] = str(thumb_height)
        replace_dict['**title**'] = title
        main_out.append(replace(entry, replace_dict))
        #
        # next we need to build the individual page
        replace_dict = {}
        replace_dict['**title**'] = title
        if i != 1:
            # not the first image
            replace_dict['<!-- **leftcomment'] = ''
            replace_dict['leftcomment** -->'] = ''
            replace_dict['**linkleft**'] = left_link
            replace_dict['**thumbleft**'] = posixjoin('../thumbnails/',
                                                        left_thumb)
            replace_dict['**widthleft**'] = left_thumb_width
            replace_dict['**heightleft**'] = left_thumb_height
            replace_dict['**titleleft**'] = left_title
        # XXXX
        replace_dict['**linkgallery**'] = config['path_back']
        if i != length:
            # not the last image
            replace_dict['<!-- **rightcomment'] = ''
            replace_dict['rightcomment** -->'] = ''
            replace_dict['**linkright**'] = right_link
            replace_dict['**thumbright**'] = posixjoin('../thumbnails/',
                                                        right_thumb)
            replace_dict['**widthright**'] = right_thumb_width
            replace_dict['**heightright**'] = right_thumb_height
            replace_dict['**titleright**'] = right_title
        #
        replace_dict['**image**'] = posixjoin('../', name)
        replace_dict['**widthmain**'] = width
        replace_dict['**heightmain**'] = height
        replace_dict['**description**'] = image['description']
        # make the substitutions in the page
        this_page = replace(page, replace_dict)
        page_path = os.path.join(html_dir, os.path.splitext(name)[0] + '.html')
        open(page_path, 'w').write(this_page)
    #
    if gallery_page:
        # are we running as a standalone ?
        gallery_template = open(config['gallery_template']).read()
        main_page = gallery_template.replace('**gallery**', ''.join(main_out))
        open(gallery_page, 'w').write(main_page)
    else:
        # or called from the plugin
        return ''.join(main_out)

###########################################################

message = '''gallery.py by Michael Foord
Written for rest2web - http://www.voidspace.org.uk/python/rest2web
    gallery.py config_name'''
DEBUG = 0

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        config_name = sys.argv[1]
        if not os.path.isfile(config_name):
            print 'File Error "%s" not found.'
            sys.exit(1)
    else:
        config_name = 'gallery.ini'
        if not os.path.isfile(config_name) and not DEBUG:
            sys.exit()
    # get the image config file
    # this will create it if it doesn't yet exist
    config = ConfigObj(config_name, file_error=DEBUG)
    if DEBUG:
        # default settings for an empty (new) config
        config['thumb_size'] = 150, 150
        config['gallery_dir'] = 'gallery'
        config['gallery_url'] = 'gallery'
        config['data_file'] = 'gallery_data.ini'
        config['page_template'] = 'page.html'
        config['entry_template'] = 'entry.html'
        config['gallery_template'] = 'gallery.html'
        config['gallery_page'] = 'test.html'
        config['gallery_mode'] = '2'
    #
    # FIXME: we *assume* the gallery dir is a single directory down
    #        so the html file is then two directories down
    #        need a better way of calculating path back
    config['path_back'] = posixjoin('../../', config['gallery_page'])
    data = get_info(config)
    # we have now created all the thumbnails and saved the config file
    make_pages(config, data)
    #


"""
ISSUES
======

Two images with the same filename but different extensions will be given the
same html page name (and so screw things up).


TODO
====

Documenting

Testing as a standalone app

'path_back' needs sorting for standalone app

Encoding needs sorting

Ought to be able to emit html in a 'rest compatible' way..

Raise an error if the scanned directory doesn't exist

``<% path_to_root %>`` (etc) not expanded in gallery files. Is there a
work-around ?


CHANGELOG
=========

2006/04/03
----------

Skip files that cause an ``IOError`` when we write out the thumbnail. This
skips animated jpg images.

2005/12/10
----------

Changed urlpath import.

Defined image_types.

2005/09/04
----------

We always regenerate thumbnails now.

2005/08/08
----------

Bug fix - now gets all images (was mising the first one).

2005/07/31
----------

It works !

"""



