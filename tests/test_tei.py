"""Tests for the XML-TEI output format (``obeliks.run(text, tei=True)``).

Current document shape (as produced by ``tokenizer.process_tei``)::

    TEI (xmlns, xml:lang="sl")
      text
        p (empty, xml:id="F<npar>")
        s (xml:id="F<npar>.<ns>")
          w | c | pc ...
        s ...
"""

import obeliks
import lxml.etree as ET

# Namespaces used in the TEI output
TEI_NS = 'http://www.tei-c.org/ns/1.0'
XML_NS = 'http://www.w3.org/XML/1998/namespace'


def test_output_is_well_formed_xml():
    raw = obeliks.run('To je stavek.', tei=True)
    assert isinstance(raw, bytes)
    root = ET.fromstring(raw)
    assert root.tag.rsplit('}', 1)[-1] == 'TEI'


def test_root_attributes():
    root = ET.fromstring(obeliks.run('To je stavek.', tei=True))
    assert root.nsmap.get(None) == TEI_NS
    assert root.get('{%s}lang' % XML_NS) == 'sl'


def test_document_structure():
    root = ET.fromstring(obeliks.run('To je stavek. Tudi to je stavek.', tei=True))
    text = root.find('{%s}text' % TEI_NS)
    assert text is not None
    # one (empty) paragraph marker per paragraph
    p = text.findall('{%s}p' % TEI_NS)
    assert len(p) == 1
    assert len(p[0]) == 0
    # sentences are children of <text>
    s = text.findall('{%s}s' % TEI_NS)
    assert len(s) == 2
    # each sentence contains words, spaces and punctuation
    localnames = [e.tag.rsplit('}', 1)[-1] for e in s[0]]
    assert localnames == ['w', 'c', 'w', 'c', 'w', 'pc', 'c']
    localnames = [e.tag.rsplit('}', 1)[-1] for e in s[1]]
    assert localnames == ['w', 'c', 'w', 'c', 'w', 'c', 'w', 'pc']


def test_multiple_paragraphs():
    root = ET.fromstring(obeliks.run('Prvi.\n\nDrugi.', tei=True))
    text = root.find('{%s}text' % TEI_NS)
    assert len(text.findall('{%s}p' % TEI_NS)) == 2
    assert len(text.findall('{%s}s' % TEI_NS)) == 2
    ps = text.findall('{%s}p' % TEI_NS)
    assert ps[0].get('{%s}id' % XML_NS) == 'F1'
    assert ps[1].get('{%s}id' % XML_NS) == 'F2'


def test_paragraph_and_sentence_ids():
    root = ET.fromstring(obeliks.run('To je stavek.', tei=True))
    text = root.find('{%s}text' % TEI_NS)
    assert text.find('{%s}p' % TEI_NS).get('{%s}id' % XML_NS) == 'F1'
    s = text.find('{%s}s' % TEI_NS)
    assert s.get('{%s}id' % XML_NS) == 'F1.1'


def test_word_and_pc_elements():
    root = ET.fromstring(obeliks.run('To je stavek.', tei=True))
    s = root.find('{%s}text' % TEI_NS).find('{%s}s' % TEI_NS)
    words = s.findall('{%s}w' % TEI_NS)
    pcs = s.findall('{%s}pc' % TEI_NS)
    assert [w.text for w in words] == ['To', 'je', 'stavek']
    assert [pc.text for pc in pcs] == ['.']


def test_word_ids():
    root = ET.fromstring(obeliks.run('To je stavek.', tei=True))
    s = root.find('{%s}text' % TEI_NS).find('{%s}s' % TEI_NS)
    ids = [w.get('{%s}id' % XML_NS) for w in s.findall('{%s}w' % TEI_NS)]
    assert ids == ['F1.1.t1', 'F1.1.t2', 'F1.1.t3']


def test_punctuation_attributes():
    root = ET.fromstring(obeliks.run('To je stavek.', tei=True))
    pc = root.find('{%s}text' % TEI_NS).find('{%s}s' % TEI_NS).find('{%s}pc' % TEI_NS)
    assert pc.get('lemma') == '.'
    assert pc.get('ana') == 'mte:Z'
    assert pc.get('msd') == 'UposTag=PUNCT'


def test_spaces_are_c_elements():
    root = ET.fromstring(obeliks.run('To je stavek.', tei=True))
    s = root.find('{%s}text' % TEI_NS).find('{%s}s' % TEI_NS)
    # one <c> per actual space in the text (between To/je and je/stavek)
    spaces = [c.text for c in s.findall('{%s}c' % TEI_NS)]
    assert spaces == [' ', ' ']


def test_symbols_are_tagged_with_ana_and_msd():
    # '>' is a symbol, not punctuation (regression from the < > fix);
    # note: unlike CoNLL-U, TEI keeps the entity form ('&gt;') as the lemma
    root = ET.fromstring(obeliks.run('5 > 4.', tei=True))
    s = root.find('{%s}text' % TEI_NS).find('{%s}s' % TEI_NS)
    pcs = s.findall('{%s}pc' % TEI_NS)
    gt = [pc for pc in pcs if pc.text == '>']
    assert len(gt) == 1
    assert gt[0].get('lemma') == '&gt;'
    assert gt[0].get('ana') == 'mte:Z'
    assert gt[0].get('msd') == 'UposTag=SYM'


def test_less_than_is_xml_escaped():
    # '<' is a symbol in the TEI output and must be XML-escaped
    root = ET.fromstring(obeliks.run('5 < 6.', tei=True))
    raw = ET.tostring(root, encoding='unicode')
    assert '&lt;' in raw
