Run r2w.py to build the docs in the docs_html folder.

Run gallery_test.bat (windows) or ``r2w.py gallery_test.ini`` to build the
gallery test files.

example_site.bat (windows) or ``r2w.py tutorial_site.ini`` creates the 
small example site used in the tutorial.

tests/file_uservalue.bat (windows) or :

``../r2w.py -t template2.txt -u "uservalue2=The real uservalue2." -u "uservalue3=A value for uservalue3." file_uservalue.ini``

This builds a simple test site exercising uservalues and the file keyword. The
output is in ``tests/file_uservalue_html``.

tests/force.bat (windows) or ``../r2w.py force.ini`` tests building a website
without a template, indexes or restindexes.
