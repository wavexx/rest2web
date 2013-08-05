#!/usr/bin/python -u

"""
smiley.py from http://www.la-la.com
As amended by Michael Foord

This version is edited to work with the Voidspace Guestbook
http://www.voidspace.org.uk/python/guestbook.html
"""

##    smiley.py
##    v0.1.0, 2005\03\31
##    A smiley library handler for phpbb style smiley paks
##    Copyright (C) 2005  Mark Andrews
##    E-mail : mark AT la-la DOT com
##    Website: http://la-la.com
##
##    For Kim for bringing me so much laughter and smiles
##
##    This software is licensed under the terms of the BSD license.
##    Basically you're free to copy, modify, distribute and relicense it,
##    So long as you keep a copy of the license with it.
##
##    Requires path.py from http://www.jorendorff.com/articles/python/path/

import re
from rest2web.modules.path import path
repak = re.compile(r'^(.*?)=\+:(.*?)=\+:(.*)')
resmile = re.compile(r'.*(:[^:]+:).*')
reno = re.compile(r'.*(<code|<pre)(\s.*?)?>.*')
reyes = re.compile(r'.*(</code>|</pre>).*')

_default_pak = '''
biggrin.gif=+:Very Happy=+::D
biggrin.gif=+:Very Happy=+::-D
biggrin.gif=+:Very Happy=+::grin:
biggrin.gif=+:Very Happy=+::biggrin:
smile.gif=+:Smile=+::)
smile.gif=+:Smile=+::-)
smile.gif=+:Smile=+::smile:
sad.gif=+:Sad=+::(
sad.gif=+:Sad=+::-(
sad.gif=+:Sad=+::sad:
surprised.gif=+:Surprised=+::o
surprised.gif=+:Surprised=+::-o
surprised.gif=+:Surprised=+::eek:
shock.gif=+:Shock=+::shock:
confused.gif=+:Confused=+::?
confused.gif=+:Confused=+::-?
confused.gif=+:Confused=+::???:
cool.gif=+:Cool=+:8)
cool.gif=+:Cool=+:8-)
cool.gif=+:Cool=+::cool:
lol.gif=+:Laughing=+::lol:
mad.gif=+:Mad=+::x
mad.gif=+:Mad=+::-X
mad.gif=+:Mad=+::mad:
razz.gif=+:Razz=+::p
razz.gif=+:Razz=+::-p
razz.gif=+:Razz=+::razz:
redface.gif=+:Embarassed=+::oops:
cry.gif=+:Crying or Very sad=+::cry:
evil.gif=+:Evil or Very Mad=+::evil:
badgrin.gif=+:Bad Grin=+::badgrin:
rolleyes.gif=+:Rolling Eyes=+::roll:
wink.gif=+:Wink=+:;)
wink.gif=+:Wink=+:;-)
wink.gif=+:Wink=+::wink:
exclaim.gif=+:Exclamation=+::!:
question.gif=+:Question=+::?:
idea.gif=+:Idea=+::idea:
arrow.gif=+:Arrow=+::arrow:
neutral.gif=+:Neutral=+::|
neutral.gif=+:Neutral=+::-|
neutral.gif=+:Neutral=+::neutral:
doubt.gif=+:Doubt=+::doubt:'''[1:].splitlines()

class lib(object):

    def __init__(self, source = None, url=None, replace=False, safe=False):
        self.sources = []
        self.clear()
        self.load(source, url, replace)

    def clear(self):
        self.smilies = {}

    def load(self, source, url=None, replace=False, safe=False):
        """
        Loads phpbb style smiley paks from directory source. Image locations
        are prepended with url. With replace set to true, later smilies with
        same key will overwrite original. With safe set to true, only smilies
        with :smile: style keys will be included.
        """
        if url is None:
            url = '/'
        elif url[len(url)-1] != '/':
            url = url + '/'
        #
        if source is not None:
            p = path(source)
            for fn in p.files('*.pak'):
                f = fn.open()
                for l in f:
                    self._parse_pak_line(l, url, safe, replace)
                f.close()
        else:
            for l in _default_pak:
                self._parse_pak_line(l, url, safe, replace)
        self.sources.append(source)

    
    def _parse_pak_line(self, l, url, safe, replace):
        s = repak.match(l)
        if s:
            key = s.groups(0)[2].strip()
            if not safe or resmile.match(key):
                if replace or not self.smilies.has_key(key):
                    self.smilies[key] = [url + s.groups(0)[0],
                                         s.groups(0)[1]]


    def parsetoken(self, t, nest=0):
        """Recursive routine to replace :smile: tags"""
        r = resmile.match(t)
        if r:
            rn = r.groups(0)[0]
            if self.smilies.has_key(rn):
                rt = self.get_tag(self.smilies[rn][0], self.smilies[rn][1])
                t = re.sub(re.escape(rn), rt, t)
                t = self.parsetoken(t, nest)
            else:
                # not a known smiley, hide and try again
                nest = nest + 1
                rt = 'smileynest' + str(nest)
                t = re.sub(re.escape(rn[:len(rn)-2]), rt, t)
                t = self.parsetoken(t, nest)
                t = re.sub(rt, rn[:len(rn)-2], t)
        return t


    def makehappy(self, text):
        """
        Replace all smiley codes in text with their image links and return
        the updated text. A :-) style smilie next to other characters will
        not be replaced. :smile: ones will. Tabs and multiple spaces will be
        replaced by a single space. <pre></pre> and <code></code> sections
        are ignored, though the start and end tags should be on individual
        lines for clean results.
        """
        buf = text.split('\n')
        text = ''
        process = True
        for l in buf:
            tokens = l.split(' ')
            if reno.match(l):
                process = False
            if reyes.match(l):
                process = True
            if process:
                tl = ''
                for t in tokens:
                    if self.smilies.has_key(t):
                        t = self.get_tag(
                            self.smilies[t][0],
                            self.smilies[t][1])
                    else:
                        t = self.parsetoken(t)
                    tl = tl + ' ' + t
                # leading space gained on first token
                text = text + tl[1:] + '\n'
            else:
                # pass code and pre sections unmodified
                text = text + l
        return text


    def get_tag(self, image, alt):
        """
        Override this if you want to add class information etc to the image
        tags
        """
        tag = '<img src="' + image + '" alt="' + alt + '" />'
        return tag

"""

CHANGELOG

2006/08/13
Added the default pak.
Removed unused method.

"""
