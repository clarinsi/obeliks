"""Tests for abbreviation handling.

Obeliks keeps the period of known abbreviations attached to the word
(``dr.``, ``itd.``) and, for a subset of them, may split the sentence
after the abbreviation depending on what follows.
"""

import obeliks


def test_dr_does_not_split_sentence():
    out = obeliks.run('dr. Novak je zdravnik.', conllu=True)
    # sentences are separated by blank lines in the output
    sents = [block for block in out.split('\n\n') if block.strip()]
    assert len(sents) == 1
    forms = [line.split('\t')[1] for line in sents[0].splitlines()
             if line and not line.startswith('#')]
    assert forms == ['dr.', 'Novak', 'je', 'zdravnik', '.']


def test_multiple_titles_are_kept_together():
    out = obeliks.run('prof. dr. Novak', conllu=True)
    forms = [line.split('\t')[1] for line in out.splitlines()
             if line and not line.startswith('#')]
    assert forms == ['prof.', 'dr.', 'Novak']


def test_itd_at_sentence_end_splits():
    out = obeliks.run('Kupi mleko, kruh itd. Potem gremo.', conllu=True)
    # sentences are separated by blank lines in the output
    sents = [[line.split('\t')[1] for line in block.splitlines()
              if line and not line.startswith('#')]
             for block in out.split('\n\n') if block.strip()]
    assert sents == [['Kupi', 'mleko', ',', 'kruh', 'itd.'], ['Potem', 'gremo', '.']]


def test_itd_mid_sentence_does_not_split():
    out = obeliks.run('Kupi mleko, kruh itd. in še kaj.', conllu=True)
    forms = [line.split('\t')[1] for line in out.splitlines()
             if line and not line.startswith('#')]
    assert forms == ['Kupi', 'mleko', ',', 'kruh', 'itd.', 'in', 'še', 'kaj', '.']


def test_npr_mid_sentence_does_not_split():
    out = obeliks.run('Piše: npr. tole.', conllu=True)
    forms = [line.split('\t')[1] for line in out.splitlines()
             if line and not line.startswith('#')]
    assert forms == ['Piše', ':', 'npr.', 'tole', '.']


def test_abbreviation_at_end_of_previous_sentence():
    out = obeliks.run('dr. Novak je zdravnik. Tudi dr. Kovač.', conllu=True)
    # sentences are separated by blank lines in the output
    sents = [[line.split('\t')[1] for line in block.splitlines()
              if line and not line.startswith('#')]
             for block in out.split('\n\n') if block.strip()]
    assert sents == [['dr.', 'Novak', 'je', 'zdravnik', '.'], ['Tudi', 'dr.', 'Kovač', '.']]


def test_dotted_sequence_with_spaces():
    out = obeliks.run('D. o. o. je podjetje.', conllu=True)
    forms = [line.split('\t')[1] for line in out.splitlines()
             if line and not line.startswith('#')]
    assert forms == ['D.', 'o.', 'o.', 'je', 'podjetje', '.']


def test_ordinal_with_dot():
    out = obeliks.run('Št. 123', conllu=True)
    forms = [line.split('\t')[1] for line in out.splitlines()
             if line and not line.startswith('#')]
    assert forms == ['Št.', '123']


def test_date_with_ordinals():
    out = obeliks.run('Danes je 15. 3. 2024.', conllu=True)
    forms = [line.split('\t')[1] for line in out.splitlines()
             if line and not line.startswith('#')]
    assert forms == ['Danes', 'je', '15.', '3.', '2024', '.']


def test_case_sensitive_abbreviation():
    # 'Jan' is in the case-sensitive abbreviation list (ListOExclCS)
    out = obeliks.run('Jan. 2020', conllu=True)
    forms = [line.split('\t')[1] for line in out.splitlines()
             if line and not line.startswith('#')]
    assert forms == ['Jan.', '2020']


def test_word_ending_with_dot_is_not_an_abbreviation():
    # 'err' is case-sensitive abbreviation, so lowercase 'err' is a normal word
    out = obeliks.run('err je napaka.', conllu=True)
    forms = [line.split('\t')[1] for line in out.splitlines()
             if line and not line.startswith('#')]
    assert forms == ['err', 'je', 'napaka', '.']


def test_abbreviated_sequence_without_spaces():
    # 'd.o.o.' written without spaces is still recognized token-by-token
    out = obeliks.run('d.o.o. je podjetje.', conllu=True)
    forms = [line.split('\t')[1] for line in out.splitlines()
             if line and not line.startswith('#')]
    assert forms == ['d.', 'o.', 'o.', 'je', 'podjetje', '.']
