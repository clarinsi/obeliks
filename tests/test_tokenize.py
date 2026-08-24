"""Tests for the default 'tokenize-only' output format.

The default output of ``obeliks.run(text)`` is a plain-text list of
tokens with positions ``<para>.<sent>.<tok>.<start>-<end>`` (1-based
character offsets into the original text), one token per line, and
blank lines between sentences.
"""

import obeliks


def test_basic_sentence_split():
    output = obeliks.run('To je stavek. Tudi to je stavek.')
    # One 'pos\ttoken' line per token; sentence 1 positions start with
    # '1.1.', sentence 2 with '1.2.'
    pairs = [line.split('\t') for line in output.splitlines() if line.strip()]
    sent1 = [token for pos, token in pairs if pos.startswith('1.1.')]
    sent2 = [token for pos, token in pairs if pos.startswith('1.2.')]
    assert sent1 == ['To', 'je', 'stavek', '.']
    assert sent2 == ['Tudi', 'to', 'je', 'stavek', '.']


def test_character_offsets_are_one_based_inclusive():
    # "To je stavek." -> 'To' spans chars 1-2, 'je' 4-5, 'stavek' 7-12, '.' 13-13
    output = obeliks.run('To je stavek.')
    positions = [line.split('\t')[0] for line in output.splitlines() if line.strip()]
    assert positions == [
        '1.1.1.1-2',   # To
        '1.1.2.4-5',   # je
        '1.1.3.7-12',  # stavek
        '1.1.4.13-13', # .
    ]


def test_multiple_paragraphs_are_separated_by_blank_lines():
    output = obeliks.run('Prvi odstavek.\n\nDrugi odstavek.')
    # Group token lines by the leading paragraph number of their position
    paras = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        pos, token = line.split('\t')
        paras.setdefault(pos.split('.')[0], []).append((pos, token))
    assert list(paras) == ['1', '2']  # two paragraphs
    assert [token for _, token in paras['1']] == ['Prvi', 'odstavek', '.']
    assert [token for _, token in paras['2']] == ['Drugi', 'odstavek', '.']
    # Paragraph numbering restarts at 2.1.* for the second paragraph
    assert all(pos.startswith('2.1.') for pos, _ in paras['2'])


def test_sentence_numbers_restart_per_paragraph():
    text = 'Prvi.\n\nDrugi. Drugi nadaljevanje.'
    paras = {}
    for line in obeliks.run(text).splitlines():
        if not line.strip():
            continue
        pos, token = line.split('\t')
        paras.setdefault(pos.split('.')[0], []).append((pos, token))
    assert [pos for pos, _ in paras['1']] == ['1.1.1.1-4', '1.1.2.5-5']
    positions = [pos for pos, _ in paras['2']]
    assert [p for p in positions if p.startswith('2.1.')]
    assert [p for p in positions if p.startswith('2.2.')]


def test_empty_input_produces_no_output():
    # Whitespace-only input yields no output; a truly empty string falls
    # back to reading stdin (see test_api), so avoid it here.
    assert obeliks.run('   \n\n  ') == ''


def test_empty_string_reads_stdin(monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO('To je stavek.'))
    out = obeliks.run('')
    assert 'stavek' in out


def test_punctuation_is_tokenized_separately():
    tokens = [line.split('\t')[1] for line in obeliks.run('Kaj? Kako!').splitlines()
              if line.strip()]
    assert tokens == ['Kaj', '?', 'Kako', '!']


def test_apostrophes_are_separate_tokens():
    tokens = [line.split('\t')[1] for line in obeliks.run("Angleški 'quoted' izraz.").splitlines()
              if line.strip()]
    assert tokens == ['Angleški', "'", 'quoted', "'", 'izraz', '.']


def test_numbers_with_separators_stay_together():
    for token in ['3.14', '4,5', '10,000', '2.0', '25,5']:
        output = obeliks.run('Vrednost je {}.'.format(token))
        tokens = [line.split('\t')[1] for line in output.splitlines() if line.strip()]
        assert token in tokens, '{} should be a single token, got {}'.format(token, tokens)


def test_schwa_is_treated_as_a_letter():
    # Regression: schwa (U+0259) used to be classified as punctuation
    tokens = [line.split('\t')[1] for line in obeliks.run('ə je šva.').splitlines()
              if line.strip()]
    assert tokens == ['ə', 'je', 'šva', '.']


def test_soft_hyphens_are_normalized_to_dashes():
    # U+00AD soft hyphen is replaced by '-' before tokenization
    tokens = [line.split('\t')[1] for line in obeliks.run('de\u00adfini\u00adcija').splitlines()
              if line.strip()]
    assert tokens == ['de', '-', 'fini', '-', 'cija']
