# -*- coding: utf-8 -*-
"""
    Based on babel.dates
    ~~~~~~~~~~~~~~~~
    :note: Adapted to suit the needs of Globalize
    :copyright: (c) 2013 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""

PATTERN_CHARS = {
    'G': [1, 2, 3, 4, 5],                                               # era
    'y': None, 'Y': None, 'u': None,                                    # year
    'Q': [1, 2, 3, 4, 5], 'q': [1, 2, 3, 4, 5],                         # quarter
    'M': [1, 2, 3, 4, 5], 'L': [1, 2, 3, 4, 5],                         # month
    'w': [1, 2], 'W': [1],                                              # week
    'd': [1, 2], 'D': [1, 2, 3], 'F': [1], 'g': None,                   # day
    'E': [1, 2, 3, 4, 5, 6], 'e': [1, 2, 3, 4, 5, 6], 'c': [1, 3, 4, 5, 6],  # week day
    'a': [1],                                                           # period
    'h': [1, 2], 'H': [1, 2], 'K': [1, 2], 'k': [1, 2],                 # hour
    'm': [1, 2],                                                        # minute
    's': [1, 2], 'S': None, 'A': None,                                  # second
    'z': [1, 2, 3, 4], 'Z': [1, 2, 3, 4, 5], 'O': [1, 4], 'v': [1, 4],  # zone
    'V': [1, 2, 3, 4], 'x': [1, 2, 3, 4, 5], 'X': [1, 2, 3, 4, 5]       # zone
}

#: The pattern characters declared in the Date Field Symbol Table
#: (http://www.unicode.org/reports/tr35/tr35-dates.html#Date_Field_Symbol_Table)
#: in order of decreasing magnitude.
PATTERN_CHAR_ORDER = "GyYuUQqMLlwWdDFgEecabBChHKkjJmsSAzZOvVXx"

_pattern_cache = {}


def untokenize_pattern(tokens):
    """
    Turn a date format pattern token stream back into a string.
    This is the reverse operation of ``tokenize_pattern``.
    :type tokens: Iterable[tuple]
    :rtype: str
    """
    output = []
    for tok_type, tok_value in tokens:
        if tok_type == "field":
            output.append(tok_value[0] * tok_value[1])
        elif tok_type == "chars":
            if not any(ch in PATTERN_CHARS for ch in tok_value):  # No need to quote
                output.append(tok_value)
            else:
                output.append("'%s'" % tok_value.replace("'", "''"))
    return "".join(output)


def split_interval_pattern(pattern):
    """
    Split an interval-describing datetime pattern into multiple pieces.
    > The pattern is then designed to be broken up into two pieces by determining the first repeating field.
    - http://www.unicode.org/reports/tr35/tr35-dates.html#intervalFormats
    >>> split_interval_pattern(u'E d.M. \u2013 E d.M.')
    [u'E d.M. \u2013 ', 'E d.M.']
    >>> split_interval_pattern("Y 'text' Y 'more text'")
    ["Y 'text '", "Y 'more text'"]
    >>> split_interval_pattern(u"E, MMM d \u2013 E")
    [u'E, MMM d \u2013 ', u'E']
    >>> split_interval_pattern("MMM d")
    ['MMM d']
    >>> split_interval_pattern("y G")
    ['y G']
    >>> split_interval_pattern(u"MMM d \u2013 d")
    [u'MMM d \u2013 ', u'd']
    :param pattern: Interval pattern string
    :return: list of "subpatterns"
    """

    seen_fields = set()
    parts = [[]]

    for tok_type, tok_value in tokenize_pattern(pattern):
        if tok_type == "field":
            if tok_value[0] in seen_fields:  # Repeated field
                parts.append([])
                seen_fields.clear()
            seen_fields.add(tok_value[0])
        parts[-1].append((tok_type, tok_value))

    return [untokenize_pattern(tokens) for tokens in parts]


def tokenize_pattern(pattern):
    """
    Tokenize date format patterns.
    Returns a list of (token_type, token_value) tuples.
    ``token_type`` may be either "chars" or "field".
    For "chars" tokens, the value is the literal value.
    For "field" tokens, the value is a tuple of (field character, repetition count).
    :param pattern: Pattern string
    :type pattern: str
    :rtype: list[tuple]
    """
    result = []
    quotebuf = None
    charbuf = []
    fieldchar = ['']
    fieldnum = [0]

    def append_chars():
        result.append(('chars', ''.join(charbuf).replace('\0', "'")))
        del charbuf[:]

    def append_field():
        result.append(('field', (fieldchar[0], fieldnum[0])))
        fieldchar[0] = ''
        fieldnum[0] = 0

    for idx, char in enumerate(pattern.replace("''", '\0')):
        if quotebuf is None:
            if char == "'":  # quote started
                if fieldchar[0]:
                    append_field()
                elif charbuf:
                    append_chars()
                quotebuf = []
            elif char in PATTERN_CHARS:
                if charbuf:
                    append_chars()
                if char == fieldchar[0]:
                    fieldnum[0] += 1
                else:
                    if fieldchar[0]:
                        append_field()
                    fieldchar[0] = char
                    fieldnum[0] = 1
            else:
                if fieldchar[0]:
                    append_field()
                charbuf.append(char)

        elif quotebuf is not None:
            if char == "'":  # end of quote
                charbuf.extend(quotebuf)
                quotebuf = None
            else:  # inside quote
                quotebuf.append(char)

    if fieldchar[0]:
        append_field()
    elif charbuf:
        append_chars()

    return result


def parse_pattern(pattern):
    """Parse date, time, and datetime format patterns.
    >>> parse_pattern("MMMMd").format
    u'%(MMMM)s%(d)s'
    >>> parse_pattern("MMM d, yyyy").format
    u'%(MMM)s %(d)s, %(yyyy)s'
    Pattern can contain literal strings in single quotes:
    >>> parse_pattern("H:mm' Uhr 'z").format
    u'%(H)s:%(mm)s Uhr %(z)s'
    An actual single quote can be used by using two adjacent single quote
    characters:
    >>> parse_pattern("hh' o''clock'").format
    u"%(hh)s o'clock"
    :param pattern: the formatting pattern to parse
    """
    if type(pattern) is DateTimePattern:
        return pattern

    if pattern in _pattern_cache:
        return _pattern_cache[pattern]

    result = []

    for tok_type, tok_value in tokenize_pattern(pattern):
        if tok_type == "chars":
            result.append(tok_value.replace('%', '%%'))
        elif tok_type == "field":
            fieldchar, fieldnum = tok_value
            limit = PATTERN_CHARS[fieldchar]
            if limit and fieldnum not in limit:
                raise ValueError('Invalid length for field: %r'
                                 % (fieldchar * fieldnum))
            result.append('%%(%s)s' % (fieldchar * fieldnum))
        else:
            raise NotImplementedError("Unknown token type: %s" % tok_type)

    _pattern_cache[pattern] = pat = DateTimePattern(pattern, u''.join(result))
    return pat


class DateTimePattern(object):

    def __init__(self, pattern, format):
        self.pattern = pattern
        self.format = format

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.pattern)

    def __unicode__(self):
        return self.pattern
