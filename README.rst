rest2web extended
=================

This is a fork of rest2web_ based off 0.5.2 alpha (r248), the last available
"development" release taken from SVN, which is also the same version as
currently available on Debian.


Changes so far
--------------

- Improved gallery plugin:

  * Does not regeneate existing thumbnails when it's not needed.
  * Ability to link directly to images instead of generating a page for each
    (which works great with javascript lightboxes).
  * Templates interpreted using ``embedded_code`` (same template engine as
    normally used in rest2web). **Incompatible change!**
  * ``thumb_dir`` and ``thumb_url`` can be customized.


The plan
--------

- RSS plugin to generate feeds from directories.
- Per-directory overrides and defaults.
- Allow external restindex so that plain "rst" files can be re-used/linked in
  the tree without editing.
- Switch all configuration/restindex/uservalues to YaML.
- Use jinja2 for templating.
- Integrate aafigure_.


.. _rest2web: http://www.voidspace.org.uk/python/rest2web/
.. _aafigure: https://launchpad.net/aafigure
