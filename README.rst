rest2web extended
=================

This is a fork of rest2web_ based off 0.5.2 alpha (r248), the last available
"development" release taken from SVN, which is also the same version as
currently available on Debian.


Changes so far
--------------

- Improved gallery plugin:

  * Do not regenerate existing thumbnails when possible (mtime-based check).
  * Ability to link directly to images instead of generating a page for each
    (which works great with javascript lightboxes).
  * Templates interpreted using ``embedded_code`` (same template engine as
    normally used in rest2web). **Incompatible change!**
  * ``thumb_dir`` and ``thumb_url`` can be customized.

- Typogrify support:

  * Supports post-processing all the output pages with `Typogrify
    <https://github.com/mintchaos/typogrify>`_.
  * A new configuration option ``typogrify`` is available and enabled by
    default in the configuration file.
  * Post-processing can also be controlled on a per-directory/page basis with
    the ``typogrify`` setting in the restindex.


The plan
--------

- Allow external restindex so that plain "rst" files can be re-used/linked in
  the tree without editing.
- Integrate aafigure_.
- Per-directory overrides and defaults.
- RSS plugin to generate feeds from directories.
- Remove configobj.
- Switch all configuration/restindex/uservalues to YaML.
- Use ``setuptools/pkg_resources``.
- Use jinja2 for templating.


.. _rest2web: http://www.voidspace.org.uk/python/rest2web/
.. _aafigure: https://launchpad.net/aafigure
