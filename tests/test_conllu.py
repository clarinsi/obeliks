"""Tests for the CoNLL-U output format (``obeliks.run(text, conllu=True)``)."""

import obeliks


def test_headers():
    lines = obeliks.run('To je stavek.', conllu=True).splitlines()
    assert lines[0] == '# newpar id = 1'
    assert lines[1] == '# sent_id = 1.1'
    assert lines[2] == '# text = To je stavek.'


def test_sentence_ids():
    out = obeliks.run('Prvi stavek. Drugi stavek.', conllu=True)
    sent_ids = [line.split('=', 1)[1].strip()
                for line in out.splitlines() if line.startswith('# sent_id = ')]
    texts = [line.split('=', 1)[1].strip()
             for line in out.splitlines() if line.startswith('# text = ')]
    assert sent_ids == ['1.1', '1.2']
    assert texts == ['Prvi stavek.', 'Drugi stavek.']


def test_every_token_line_has_ten_columns():
    out = obeliks.run('To je stavek. Tudi to je stavek.', conllu=True)
    rows = [line.split('\t') for line in out.splitlines()
            if line and not line.startswith('#')]
    assert len(rows) == 9
    assert all(len(r) == 10 for r in rows)


def test_plain_words_have_underscore_attributes():
    out = obeliks.run('To je stavek.', conllu=True)
    rows = [line.split('\t') for line in out.splitlines()
            if line and not line.startswith('#')]
    # id, form, lemma, upos, xpos, feats, head, deprel, deps, misc
    assert rows[0] == ['1', 'To', '_', '_', '_', '_', '_', '_', '_', '_']


def test_punctuation_gets_lemma_upos_xpos():
    out = obeliks.run('To je stavek.', conllu=True)
    rows = [line.split('\t') for line in out.splitlines()
            if line and not line.startswith('#')]
    # id, form, lemma, upos, xpos, feats, head, deprel, deps, misc
    assert rows[3] == ['4', '.', '.', 'PUNCT', 'Z', '_', '_', '_', '_', '_']


def test_space_after_no_before_punctuation():
    out = obeliks.run('To je stavek.', conllu=True)
    rows = [line.split('\t') for line in out.splitlines()
            if line and not line.startswith('#')]
    assert rows[2][9] == 'SpaceAfter=No'  # misc column: 'stavek' before '.'
    assert rows[3][9] == '_'              # '.' is the last token
    assert rows[0][9] == '_'              # 'To' is followed by a space
    assert rows[1][9] == '_'              # 'je' is followed by a space


def test_space_after_no_after_punctuation():
    # comma is immediately followed by a space, the word before it has no space after
    out = obeliks.run('Kupi mleko, kruh.', conllu=True)
    rows = [line.split('\t') for line in out.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['Kupi', 'mleko', ',', 'kruh', '.']
    assert rows[1][9] == 'SpaceAfter=No'  # 'mleko' before ','
    assert rows[2][9] == '_'              # ',' followed by space


def test_slovenian_characters_are_words():
    out = obeliks.run('Škofja Loka je lepo mesto.', conllu=True)
    rows = [line.split('\t') for line in out.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['Škofja', 'Loka', 'je', 'lepo', 'mesto', '.']
    # none of the words are tagged as symbols/punctuation
    assert all(r[3] == '_' for r in rows[:5])  # upos column


def test_quotes_are_punctuation():
    out = obeliks.run('Stavek s "narekovaji".', conllu=True)
    rows = [line.split('\t') for line in out.splitlines()
            if line and not line.startswith('#')]
    quotes = [r for r in rows if r[1] == '"']
    assert len(quotes) == 2
    assert all(r[3] == 'PUNCT' and r[4] == 'Z' for r in quotes)  # upos, xpos


def test_colon_and_comma_are_punctuation():
    out = obeliks.run('Naslov: Novi trg 3, 1000 Ljubljana.', conllu=True)
    rows = [line.split('\t') for line in out.splitlines()
            if line and not line.startswith('#')]
    for r in rows:
        if r[1] in (':', ','):
            assert r[3] == 'PUNCT'  # upos
            assert r[4] == 'Z'      # xpos
