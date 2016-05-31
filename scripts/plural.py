# -*- coding: utf-8 -*-
"""
    based on babel.plural
    ~~~~~~~~~~~~~
    :note: Adapted to suit the needs of Globalize
    :copyright: (c) 2013 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
import re


_plural_tags = ('zero', 'one', 'two', 'few', 'many', 'other')
_fallback_tag = 'other'


class PluralRule(object):
    """Represents a set of language pluralization rules.  The constructor
    accepts a list of (tag, expr) tuples or a dict of `CLDR rules`_. The
    resulting object is callable and accepts one parameter with a positive or
    negative number (both integer and float) for the number that indicates the
    plural form for a string and returns the tag for the format:
    >>> rule = PluralRule({'one': 'n is 1'})
    >>> rule(1)
    'one'
    >>> rule(2)
    'other'
    Currently the CLDR defines these tags: zero, one, two, few, many and
    other where other is an implicit default.  Rules should be mutually
    exclusive; for a given numeric value, only one rule should apply (i.e.
    the condition should only be true for one of the plural rule elements.
    .. _`CLDR rules`: http://www.unicode.org/reports/tr35/tr35-33/tr35-numbers.html#Language_Plural_Rules
    """

    __slots__ = ('abstract', '_func')

    def __init__(self, rules):
        """Initialize the rule instance.
        :param rules: a list of ``(tag, expr)``) tuples with the rules
                      conforming to UTS #35 or a dict with the tags as keys
                      and expressions as values.
        :raise RuleError: if the expression is malformed
        """
        if isinstance(rules, dict):
            rules = rules.items()
        found = set()
        self.abstract = []
        for key, expr in sorted(list(rules)):
            if key not in _plural_tags:
                raise ValueError('unknown tag %r' % key)
            elif key in found:
                raise ValueError('tag %r defined twice' % key)
            found.add(key)
            ast = _Parser(expr).ast
            if ast:
                self.abstract.append((key, ast))

    def __repr__(self):
        rules = self.rules
        return '<%s %r>' % (
            type(self).__name__,
            ', '.join(['%s: %s' % (tag, rules[tag]) for tag in _plural_tags
                       if tag in rules])
        )

    @property
    def rules(self):
        """The `PluralRule` as a dict of unicode plural rules.
        >>> rule = PluralRule({'one': 'n is 1'})
        >>> rule.rules
        {'one': 'n is 1'}
        """
        _compile = _UnicodeCompiler().compile
        return dict([(tag, _compile(ast)) for tag, ast in self.abstract])

    tags = property(lambda x: frozenset([i[0] for i in x.abstract]), doc="""
        A set of explicitly defined tags in this rule.  The implicit default
        ``'other'`` rules is not part of this set unless there is an explicit
        rule for it.""")

    def __getstate__(self):
        return self.abstract

    def __setstate__(self, abstract):
        self.abstract = abstract


class RuleError(Exception):
    """Raised if a rule is malformed."""

_VARS = 'nivwft'

_RULES = [
    (None, re.compile(r'\s+(?u)')),
    ('word', re.compile(r'\b(and|or|is|(?:with)?in|not|mod|[{0}])\b'
                        .format(_VARS))),
    ('value', re.compile(r'\d+')),
    ('symbol', re.compile(r'%|,|!=|=')),
    ('ellipsis', re.compile(r'\.{2,3}|\u2026', re.UNICODE))  # U+2026: ELLIPSIS
]


def tokenize_rule(s):
    s = s.split('@')[0]
    result = []
    pos = 0
    end = len(s)
    while pos < end:
        for tok, rule in _RULES:
            match = rule.match(s, pos)
            if match is not None:
                pos = match.end()
                if tok:
                    result.append((tok, match.group()))
                break
        else:
            raise RuleError('malformed CLDR pluralization rule.  '
                            'Got unexpected %r' % s[pos])
    return result[::-1]


def test_next_token(tokens, type_, value=None):
    return tokens and tokens[-1][0] == type_ and \
           (value is None or tokens[-1][1] == value)


def skip_token(tokens, type_, value=None):
    if test_next_token(tokens, type_, value):
        return tokens.pop()


def value_node(value):
    return 'value', (value, )


def ident_node(name):
    return name, ()


def range_list_node(range_list):
    return 'range_list', range_list


def negate(rv):
    return 'not', (rv,)


class _Parser(object):
    """Internal parser.  This class can translate a single rule into an abstract
    tree of tuples. It implements the following grammar::
        condition     = and_condition ('or' and_condition)*
                        ('@integer' samples)?
                        ('@decimal' samples)?
        and_condition = relation ('and' relation)*
        relation      = is_relation | in_relation | within_relation
        is_relation   = expr 'is' ('not')? value
        in_relation   = expr (('not')? 'in' | '=' | '!=') range_list
        within_relation = expr ('not')? 'within' range_list
        expr          = operand (('mod' | '%') value)?
        operand       = 'n' | 'i' | 'f' | 't' | 'v' | 'w'
        range_list    = (range | value) (',' range_list)*
        value         = digit+
        digit         = 0|1|2|3|4|5|6|7|8|9
        range         = value'..'value
        samples       = sampleRange (',' sampleRange)* (',' ('…'|'...'))?
        sampleRange   = decimalValue '~' decimalValue
        decimalValue  = value ('.' value)?
    - Whitespace can occur between or around any of the above tokens.
    - Rules should be mutually exclusive; for a given numeric value, only one
      rule should apply (i.e. the condition should only be true for one of
      the plural rule elements).
    - The in and within relations can take comma-separated lists, such as:
      'n in 3,5,7..15'.
    - Samples are ignored.
    The translator parses the expression on instanciation into an attribute
    called `ast`.
    """

    def __init__(self, string):
        self.tokens = tokenize_rule(string)
        if not self.tokens:
            # If the pattern is only samples, it's entirely possible
            # no stream of tokens whatsoever is generated.
            self.ast = None
            return
        self.ast = self.condition()
        if self.tokens:
            raise RuleError('Expected end of rule, got %r' %
                            self.tokens[-1][1])

    def expect(self, type_, value=None, term=None):
        token = skip_token(self.tokens, type_, value)
        if token is not None:
            return token
        if term is None:
            term = repr(value is None and type_ or value)
        if not self.tokens:
            raise RuleError('expected %s but end of rule reached' % term)
        raise RuleError('expected %s but got %r' % (term, self.tokens[-1][1]))

    def condition(self):
        op = self.and_condition()
        while skip_token(self.tokens, 'word', 'or'):
            op = 'or', (op, self.and_condition())
        return op

    def and_condition(self):
        op = self.relation()
        while skip_token(self.tokens, 'word', 'and'):
            op = 'and', (op, self.relation())
        return op

    def relation(self):
        left = self.expr()
        if skip_token(self.tokens, 'word', 'is'):
            return skip_token(self.tokens, 'word', 'not') and 'isnot' or 'is', \
                   (left, self.value())
        negated = skip_token(self.tokens, 'word', 'not')
        method = 'in'
        if skip_token(self.tokens, 'word', 'within'):
            method = 'within'
        else:
            if not skip_token(self.tokens, 'word', 'in'):
                if negated:
                    raise RuleError('Cannot negate operator based rules.')
                return self.newfangled_relation(left)
        rv = 'relation', (method, left, self.range_list())
        return negate(rv) if negated else rv

    def newfangled_relation(self, left):
        if skip_token(self.tokens, 'symbol', '='):
            negated = False
        elif skip_token(self.tokens, 'symbol', '!='):
            negated = True
        else:
            raise RuleError('Expected "=" or "!=" or legacy relation')
        rv = 'relation', ('in', left, self.range_list())
        return negate(rv) if negated else rv

    def range_or_value(self):
        left = self.value()
        if skip_token(self.tokens, 'ellipsis'):
            return left, self.value()
        else:
            return left, left

    def range_list(self):
        range_list = [self.range_or_value()]
        while skip_token(self.tokens, 'symbol', ','):
            range_list.append(self.range_or_value())
        return range_list_node(range_list)

    def expr(self):
        word = skip_token(self.tokens, 'word')
        if word is None or word[1] not in _VARS:
            raise RuleError('Expected identifier variable')
        name = word[1]
        if skip_token(self.tokens, 'word', 'mod'):
            return 'mod', ((name, ()), self.value())
        elif skip_token(self.tokens, 'symbol', '%'):
            return 'mod', ((name, ()), self.value())
        return ident_node(name)

    def value(self):
        return value_node(int(self.expect('value')[1]))


def _binary_compiler(tmpl):
    """Compiler factory for the `_Compiler`."""
    return lambda self, l, r: tmpl % (self.compile(l), self.compile(r))


def _unary_compiler(tmpl):
    """Compiler factory for the `_Compiler`."""
    return lambda self, x: tmpl % self.compile(x)


compile_zero = lambda x: '0'


class _Compiler(object):
    """The compilers are able to transform the expressions into multiple
    output formats.
    """

    def compile(self, arg):
        op, args = arg
        return getattr(self, 'compile_' + op)(*args)

    compile_n = lambda x: 'n'
    compile_i = lambda x: 'i'
    compile_v = lambda x: 'v'
    compile_w = lambda x: 'w'
    compile_f = lambda x: 'f'
    compile_t = lambda x: 't'
    compile_value = lambda x, v: str(v)
    compile_and = _binary_compiler('(%s && %s)')
    compile_or = _binary_compiler('(%s || %s)')
    compile_not = _unary_compiler('(!%s)')
    compile_mod = _binary_compiler('(%s %% %s)')
    compile_is = _binary_compiler('(%s == %s)')
    compile_isnot = _binary_compiler('(%s != %s)')

    def compile_relation(self, method, expr, range_list):
        raise NotImplementedError()


class _UnicodeCompiler(_Compiler):
    """Returns a unicode pluralization rule again."""

    # XXX: this currently spits out the old syntax instead of the new
    # one.  We can change that, but it will break a whole bunch of stuff
    # for users I suppose.

    compile_is = _binary_compiler('%s is %s')
    compile_isnot = _binary_compiler('%s is not %s')
    compile_and = _binary_compiler('%s and %s')
    compile_or = _binary_compiler('%s or %s')
    compile_mod = _binary_compiler('%s mod %s')

    def compile_not(self, relation):
        return self.compile_relation(negated=True, *relation[1])

    def compile_relation(self, method, expr, range_list, negated=False):
        ranges = []
        for item in range_list[1]:
            if item[0] == item[1]:
                ranges.append(self.compile(item[0]))
            else:
                ranges.append('%s..%s' % tuple(map(self.compile, item)))
        return '%s%s %s %s' % (
            self.compile(expr), negated and ' not' or '',
            method, ','.join(ranges)
        )
