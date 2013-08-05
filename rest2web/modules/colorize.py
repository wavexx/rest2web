"""
    MoinMoin - Python Source Parser

    Created 2001 by Juergen Hermann <jh@web.de>
    Subject to the Activestate Python Cookbook License
    
    Original source: 
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52298
    Modifications by: 
        Hans Nowak, Michael Foord
"""

# Imports
import cgi, StringIO, keyword, token, tokenize


#############################################################################
### Python Source Parser (does Hilighting)
#############################################################################

_KEYWORD = token.NT_OFFSET + 1
_TEXT    = token.NT_OFFSET + 2

# define these in a stylesheet
_tags = {
    token.NUMBER: 'pynumber',
    token.OP: 'pyoperator',
    token.STRING: 'pystring',
    tokenize.COMMENT: 'pycomment',
    tokenize.ERRORTOKEN: 'pyerror',
    _KEYWORD: 'pykeyword',
    _TEXT: 'pytext',
}


class Parser:
    """
        Send colored python source.
    """

    def __init__(self, raw):
        """ Store the source text.
        """
        self.out = StringIO.StringIO()
        self.raw = raw.expandtabs().strip()

    def getvalue(self):
        return self.out.getvalue()

    def format(self, formatter, form):
        """ Parse and send the colored source.
        """
        # store line offsets in self.lines
        self.lines = [0, 0]
        pos = 0
        while 1:
            pos = self.raw.find('\n', pos) + 1
            if not pos: break
            self.lines.append(pos)
        self.lines.append(len(self.raw))
        #
        # parse the source and write it
        self.pos = 0
        text = StringIO.StringIO(self.raw)
        self.out.write('<div class="pysrc">')
        try:
            tokenize.tokenize(text.readline, self)
        except tokenize.TokenError, ex:
            msg = ex[0]
            line = ex[1][0]
            print >> self.out, ("<h3>ERROR: %s</h3>%s" %
                (msg, self.raw[self.lines[line]:]))
        self.out.write('</div>')

    def __call__(self, toktype, toktext, (srow,scol), (erow,ecol), line):
        """ Token handler.
        """
        if 0:
            print "type", toktype, token.tok_name[toktype], "text", toktext,
            print "start", srow,scol, "end", erow,ecol, "<br>"
        #
        # calculate new positions
        oldpos = self.pos
        newpos = self.lines[srow] + scol
        self.pos = newpos + len(toktext)
        #
        # handle newlines
        if toktype in [token.NEWLINE, tokenize.NL]:
            print >> self.out, ""
            return
        #
        # send the original whitespace, if needed
        if newpos > oldpos:
            self.out.write(self.raw[oldpos:newpos])
        #
        # skip indenting tokens
        if toktype in [token.INDENT, token.DEDENT]:
            self.pos = newpos
            return
        #
        # map token type to a color group
        if token.LPAR <= toktype and toktype <= token.OP:
            toktype = token.OP
        elif toktype == token.NAME and keyword.iskeyword(toktext):
            toktype = _KEYWORD
        style = _tags.get(toktype, _tags[_TEXT])
        #
        # send text
        self.out.write('<span class="%s">' % (style,))
        self.out.write(cgi.escape(toktext))
        self.out.write('</span>')


if __name__ == "__main__":
    import os, sys

    # open own source
    source = open(sys.argv[0]).read()
    #
    # write colorized version to "python.html"
    p = Parser(source)
    p.format(None, None)
    f = open('python.html', 'wt')
    f.write(p.getvalue())
    f.close()
    #
    # load HTML page into browser
    if os.name == "nt":
        os.system("explorer python.html")
    else:
        # XXXX some assumption...
        os.system("netscape python.html &")

"""
2005/06/20
Changed license text to Activestate Python Cookbook

2005/06/18
Changes by Nicola Larosa
    Code cleanup
        lines shortened
        empty comments in empty lines
        usage of string module removed

2005/03/24
Changes by Michael Foord
``<pre class="pysrc"> </pre>`` changed to ``<div class="pysrc"> </div>``
cStringIO changed to StringIO for unicode compatibility.
"""

