"""Tests for the public ``obeliks.run`` API: output targets (string,
file, stdout), object output, file input and newdoc handling.
"""

import io

import obeliks


def test_returns_string_when_no_output_target():
    out = obeliks.run('To je stavek.')
    assert isinstance(out, str)
    assert 'stavek' in out


def test_conllu_returns_string():
    out = obeliks.run('To je stavek.', conllu=True)
    assert isinstance(out, str)
    assert '# newpar id = 1' in out


def test_tei_returns_bytes():
    out = obeliks.run('To je stavek.', tei=True)
    assert isinstance(out, bytes)
    assert b'<TEI' in out


def test_object_output_structure():
    docs = obeliks.run('To je stavek.', object_output=True)
    assert isinstance(docs, list)
    assert len(docs) == 1
    doc = docs[0]
    assert len(doc) == 1  # one sentence
    sent = doc[0]
    assert sent['metadata'].startswith('# newpar id = 1\n# sent_id = 1.1\n')
    toks = sent['sentence']
    assert [t['text'] for t in toks] == ['To', 'je', 'stavek', '.']


def test_object_output_character_offsets():
    docs = obeliks.run('To je stavek.', object_output=True)
    toks = docs[0][0]['sentence']
    # (start_char, end_char) pairs into the original text
    assert [(t['start_char'], t['end_char']) for t in toks] == [
        (0, 2),   # To
        (3, 5),   # je
        (6, 12),  # stavek
        (12, 13), # .
    ]


def test_object_output_misc():
    docs = obeliks.run('To je stavek.', object_output=True)
    toks = docs[0][0]['sentence']
    assert toks[2]['misc'] == 'SpaceAfter=No'  # 'stavek' before '.'
    assert toks[3]['misc'] == '_'
    assert toks[0]['misc'] == '_'


def test_object_output_attributes():
    docs = obeliks.run('To je stavek.', object_output=True)
    toks = docs[0][0]['sentence']
    assert toks[3]['text'] == '.'
    assert toks[3]['lemma'] == '.'
    assert toks[3]['upos'] == 'PUNCT'
    assert toks[3]['xpos'] == 'Z'
    assert toks[0]['lemma'] == '_'
    assert toks[0]['upos'] == '_'


def test_out_file(tmp_path):
    out_file = tmp_path / 'out.txt'
    result = obeliks.run('To je stavek.', out_file=str(out_file))
    assert result is None
    content = out_file.read_text(encoding='utf-8')
    assert 'stavek' in content


def test_out_file_conllu(tmp_path):
    out_file = tmp_path / 'out.conllu'
    obeliks.run('To je stavek.', out_file=str(out_file), conllu=True)
    content = out_file.read_text(encoding='utf-8')
    assert '# newpar id = 1' in content
    assert '\tstavek\t' in content


def test_to_stdout(capsys):
    result = obeliks.run('To je stavek.', to_stdout=True)
    assert result is None
    captured = capsys.readouterr()
    assert 'stavek' in captured.out


def test_in_file(tmp_path):
    in_file = tmp_path / 'in.txt'
    in_file.write_text('To je stavek.', encoding='utf-8')
    out = obeliks.run(in_file=str(in_file), conllu=True)
    assert '# text = To je stavek.' in out


def test_in_files(tmp_path):
    f1 = tmp_path / 'a.txt'
    f2 = tmp_path / 'b.txt'
    f1.write_text('Prvi stavek.', encoding='utf-8')
    f2.write_text('Drugi stavek.', encoding='utf-8')
    out = obeliks.run(in_files=[str(f1), str(f2)], conllu=True)
    # one '# text = ...' metadata line per input file
    texts = [line.split('=', 1)[1].strip()
             for line in out.splitlines() if line.startswith('# text = ')]
    assert texts == ['Prvi stavek.', 'Drugi stavek.']


def test_pass_newdoc_id():
    text = '# newdoc id = 1\nTo je stavek.\n# newdoc id = 2\nDrugi stavek.'
    out = obeliks.run(text, conllu=True, pass_newdoc_id=True)
    # newdoc lines are passed through to the output (one line per occurrence)
    newdoc_lines = [l for l in out.splitlines() if l.startswith('# newdoc id = ')]
    assert len(newdoc_lines) == 2
    # paragraph numbering restarts after each newdoc line
    newpars = [line.split('=', 1)[1].strip()
               for line in out.splitlines() if line.startswith('# newpar id = ')]
    assert newpars == ['1', '2', '1', '2']


def test_unicode_input():
    out = obeliks.run('Škofja Loka – lepo mesto.', conllu=True)
    assert 'Škofja' in out
    assert 'lepo' in out


def test_multiline_input_treats_blank_lines_as_paragraph_separators():
    out = obeliks.run('Prvi.\n\nDrugi.', conllu=True)
    newpars = [line.split('=', 1)[1].strip()
               for line in out.splitlines() if line.startswith('# newpar id = ')]
    sent_ids = [line.split('=', 1)[1].strip()
                for line in out.splitlines() if line.startswith('# sent_id = ')]
    assert newpars == ['1', '2']
    assert sent_ids == ['1.1', '2.1']
