"""Tests for special token types: URLs, e-mail addresses, hashtags,
mentions, emojis, comparison signs and numeric expressions.
"""

import obeliks


def test_email_is_single_token():
    output = obeliks.run('Kontaktirajte nas na info@obeliks.si.', conllu=True)
    # token lines are the non-empty lines that don't start with '#'
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['Kontaktirajte', 'nas', 'na', 'info@obeliks.si', '.']
    email = rows[3]
    assert email[2] == 'info@obeliks.si'  # lemma
    assert email[3] == 'SYM'              # upos
    assert email[4] == 'Xw'               # xpos


def test_url_without_scheme():
    output = obeliks.run('Obiskali smo www.obeliks.si.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['Obiskali', 'smo', 'www.obeliks.si', '.']
    url = rows[2]
    assert url[2] == 'www.obeliks.si'  # lemma
    assert url[3] == 'SYM'             # upos
    assert url[4] == 'Xw'              # xpos


def test_url_with_scheme_and_path():
    output = obeliks.run('Pojdi na http://obeliks.si/abc zdaj.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['Pojdi', 'na', 'http://obeliks.si/abc', 'zdaj', '.']
    url = rows[2]
    assert url[3] == 'SYM'  # upos
    assert url[4] == 'Xw'   # xpos


def test_hashtag():
    output = obeliks.run('#prvič na Twitterju.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['#prvič', 'na', 'Twitterju', '.']
    tag = rows[0]
    assert tag[2] == '#prvič'  # lemma
    assert tag[3] == 'SYM'     # upos
    assert tag[4] == 'Xh'      # xpos


def test_mention():
    output = obeliks.run('@obeliks odgovarja.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['@obeliks', 'odgovarja', '.']
    mention = rows[0]
    assert mention[2] == '@obeliks'  # lemma
    assert mention[3] == 'SYM'       # upos
    assert mention[4] == 'Xa'        # xpos


def test_emoji():
    output = obeliks.run('To je super! 😀', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['To', 'je', 'super', '!', '😀']
    emoji = rows[4]
    assert emoji[2] == '😀'  # lemma
    assert emoji[3] == 'SYM'  # upos
    assert emoji[4] == 'Xe'   # xpos


def test_emoji_without_space():
    output = obeliks.run('Živjo!🙂', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['Živjo', '!', '🙂']
    assert rows[2][4] == 'Xe'  # xpos


def test_less_than_and_greater_than_are_symbols():
    # Regression: '<' and '>' used to be assigned PUNCT with a wrong lemma
    output = obeliks.run('5 < 6 in 6 > 5.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    lt = [r for r in rows if r[1] == '<']
    gt = [r for r in rows if r[1] == '>']
    assert len(lt) == 1 and len(gt) == 1
    assert lt[0][2] == '<' and lt[0][3] == 'SYM' and lt[0][4] == 'Z'  # lemma, upos, xpos
    assert gt[0][2] == '>' and gt[0][3] == 'SYM' and gt[0][4] == 'Z'


def test_ampersand_is_a_symbol():
    # 'T' is a single letter, so its period stays attached ('T.')
    output = obeliks.run('AT&T.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['AT', '&', 'T.']
    amp = [r for r in rows if r[1] == '&'][0]
    assert amp[3] == 'SYM'  # upos


def test_decimal_number_with_comma():
    output = obeliks.run('Ocena: 4,5.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['Ocena', ':', '4,5', '.']
    assert rows[2][3] == '_'  # upos: plain number, no tag


def test_decimal_number_with_dot():
    output = obeliks.run('Pi je 3.14.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['Pi', 'je', '3.14', '.']


def test_thousands_separator():
    output = obeliks.run('10,000 ljudi.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert [r[1] for r in rows] == ['10,000', 'ljudi', '.']


def test_schwa_is_not_punctuation():
    # Regression: schwa (U+0259) was being treated as punctuation
    output = obeliks.run('ə je šva.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert rows[0][1] == 'ə'
    assert rows[0][3] == '_'  # upos: a plain word, not PUNCT/SYM


def test_compound_word_with_hyphen():
    # Brioni rule: possessive suffixes attached with a hyphen stay together
    output = obeliks.run('To je Janezov-ov.', conllu=True)
    rows = [line.split('\t') for line in output.splitlines()
            if line and not line.startswith('#')]
    assert 'Janezov-ov' in [r[1] for r in rows]


def test_tokenize_only_and_conllu_agree_on_forms():
    text = 'To je stavek. Tudi to je stavek.'
    only = [line.split('\t')[1] for line in obeliks.run(text).splitlines() if line.strip()]
    conllu = [line.split('\t')[1] for line in obeliks.run(text, conllu=True).splitlines()
              if line and not line.startswith('#')]
    assert only == conllu
