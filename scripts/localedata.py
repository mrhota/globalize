# -*- coding: utf-8 -*-
"""
    based on babel.localedata
    ~~~~~~~~~~~~~~~~
    :note: Adapted to suit the needs of Globalize
    :copyright: (c) 2013 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""


class Alias(object):
    """Representation of an alias in the locale data.
    An alias is a value that refers to some other part of the locale data,
    as specified by the `keys`.
    """

    def __init__(self, keys):
        self.keys = tuple(keys)

    def __repr__(self):
        return '<%s %r>' % ('Alias', self.keys)