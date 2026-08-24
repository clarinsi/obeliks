"""Structural tests for the tokenization rule files.

These guard the recent refactoring of ``obeliks/res/*.txt``: character
classes were collapsed from long lists of single code points into
compact ranges, the suffix alternations were sorted alphabetically,
and the emoji character class was deduplicated. The checks are purely
structural and do not depend on tokenizer internals.
"""

import re
from pathlib import Path

RES = Path(__file__).parent.parent / 'obeliks' / 'res'

RANGE_RE = re.compile(r'\\(?:u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})')


def read_res(name):
    with open(RES / name, encoding='utf-8') as f:
        return f.read()


def rule_lines(text, prefix):
    return [l for l in text.splitlines() if l.startswith(prefix)]


def alternatives(rule):
    """Alternatives of a rule whose search part ends in
    ``<w>(<alt1>|<alt2>|...)</w>`` (rule format: search == > replacement)."""
    search = rule.split('==>')[0]
    chunk = search.split('<w>')[-1]
    alternation = chunk[:chunk.index('</w>')]
    return re.findall(r'\(([^()]*)\)', alternation)


def test_letter_suffixes_are_sorted_and_unique():
    rules = rule_lines(read_res('TokRulesPart1.txt'), '<w>([^<]+)</w>')
    assert len(rules) == 1
    alts = alternatives(rules[0])
    # update the count when intentionally extending the suffix list
    assert len(alts) == 154
    assert len(set(alts)) == len(alts)  # no duplicates
    assert alts == sorted(alts)


def test_digit_suffixes_are_sorted_and_unique():
    rules = rule_lines(read_res('TokRulesPart1.txt'), '<w>(\\d+)</w>')
    assert len(rules) == 1
    alts = alternatives(rules[0])
    assert len(alts) == 22
    assert len(set(alts)) == len(alts)
    assert alts == sorted(alts)


def test_punctuation_classes_use_compact_ranges():
    # The classes were refactored from ~100 single code points into
    # ranges; keep them compact (27 and 35 tokens respectively now).
    for name, prefix, limit in [('TokRulesPart1.txt', '([[\\u0000', 30),
                                ('TokRulesPart3.txt', '<c>([[\\u0000', 40)]:
        text = read_res(name)
        lines = rule_lines(text, prefix)
        assert len(lines) == 1, name
        tokens = RANGE_RE.findall(lines[0])
        assert len(tokens) <= limit, (name, len(tokens))


def test_emoji_class_has_no_duplicate_code_points():
    p3 = read_res('TokRulesPart3.txt')
    lines = rule_lines(p3, '<w>([\\u231A')
    assert len(lines) == 1
    tokens = RANGE_RE.findall(lines[0])
    assert len(tokens) == len(set(tokens)), 'duplicate code points in emoji class'


def test_comment_lines_use_single_hash():
    # no '##'/'###' comment markers (the Part3 header used to start with '###');
    # lines starting with '#(' are commented-out rules and are allowed
    for name in ['TokRulesPart1.txt', 'TokRulesPart2.txt', 'TokRulesPart3.txt']:
        for line in read_res(name).splitlines():
            stripped = line.lstrip()
            if stripped.startswith('#'):
                assert not stripped.startswith('##'), (name, stripped)
