rest2web extended
=================

This is a fork of rest2web_ based off 0.5.2 alpha (r248), the last available
"development" release taken from SVN, which is also the same version as
currently available on Debian.

The plan:

- Improved gallery plugin:

  * Do not regeneate thumbnails when it's not needed.
  * Ability to link directly to images instead of generating a page for each
    (which works great with javascript lightboxes).

- RSS plugin to generate feeds from directories.
- Per-directory overrides and defaults.
- Allow external restindex so that plain "rst" files can be re-used/linked in
  the tree without editing.
- Switch all configuration/restindex/uservalues to YaML.
- Use jinja2 for templating.

.. _rest2web: http://www.voidspace.org.uk/python/rest2web/
