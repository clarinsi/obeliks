import sys
import regex as re
import lxml.etree as ET
from io import StringIO

from . rules import tokenize

token_regex = re.compile(r'<S/>|</?s>|<([wc]([\s]*|[\s]+[^>]*))>([^<]+)</[wc]>')

def create_tei_tree():
    root = ET.Element('TEI')
    root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
    #root.set('xml:lang', 'sl')
    attr = root.attrib
    attr['{http://www.w3.org/XML/1998/namespace}lang'] = "sl"
    root.append(ET.Element('text'))
    return ET.ElementTree(root)


def index_of(string, substring, from_idx, val):
    substring = re.sub(r'&amp;', '&', substring) 
    substring = re.sub(r'&lt;', '<', substring) 
    substring = re.sub(r'&gt;', '>', substring) 
    val[0] = substring
    return string.find(substring, from_idx)


def unescape_xml_chars(input_str):
    return input_str.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')


def preprocess_tokens(tokens):
    stoken_regex = re.compile(r'<s>.*?</s>')

    org_text = []
    for match in stoken_regex.finditer(tokens):
        val = match.group()
        val = re.sub(r'<s>', '', val)
        val = re.sub(r'</s>', '', val)
        val = re.sub(r'<[cw]([\s]*|[\s]+[^>]*)>', '', val)
        val = re.sub(r'</w>', '', val)
        val = re.sub(r'</c>', '', val)
        val = re.sub(r'<S/>', ' ', val)
        val = re.sub(r' {2,}', ' ', val)
        val = re.sub(r' +', ' ', val)
        org_text.append(val.strip())

    return org_text

def process_tokenize_only(para, np, os):
    if para.startswith(u"\uFEFF"):
        para = para[1:]

    tokens = tokenize(para)
    org_text = preprocess_tokens(tokens)

    idx = 0
    ns = 1
    nt = 0
    old_ns = 1
    has_output = False
    for match in token_regex.finditer(tokens):
        val = match.group()
        if val == '<s>':
            nt = 0
            if ns != old_ns:
                os.write('\n')
                old_ns = ns
        elif val == '</s>':
            ns += 1
        elif val == '<S/>':
            pass
        else:
            val = match.group(3)
            actual_val = ['']
            idx_of_token = index_of(para, val, idx, actual_val)
            if idx_of_token == -1:
                print('Warning: Cannot compute token index. Token: "{}" Text: "{}"'.format(val, para))
            idx = max(idx, idx_of_token + len(actual_val[0]))
            idx_of_token += 1
            nt += 1
            line = str(np) + '.' + str(ns) + '.' + str(nt) + '.' + str(idx_of_token) + '-' + \
                    str(idx_of_token + len(actual_val[0]) - 1) + '\t' + actual_val[0] + '\n'
            os.write(line)
            has_output = True

    if has_output:
        os.write('\n')


def process_conllu(para, np, os, object_output=False):
    if para.startswith(u"\uFEFF"):
        para = para[1:]

    para_concat = ''.join(para)

    tokens = tokenize(para)

    if object_output:
        metadata = '# newpar id = {}\n'.format(np)
        doc = []
        doc_sent = []
    else:
        os.write('# newpar id = {}\n'.format(np))

    org_text = preprocess_tokens(tokens)

    idx = 0
    ns = 1
    nt = 0
    old_ns = 1
    has_output = False
    for match in token_regex.finditer(tokens):
        val = match.group()
        if val == '<s>':
            nt = 0
            if ns != old_ns:
                if not object_output:
                    os.write('\n')
                old_ns = ns
            if object_output:
                metadata += '# sent_id = {}.{}\n'.format(np, ns)
                metadata += '# text = {}\n'.format(unescape_xml_chars(org_text[ns - 1]))
            else:
                os.write('# sent_id = {}.{}\n'.format(np, ns))
                os.write('# text = {}\n'.format(unescape_xml_chars(org_text[ns - 1])))
        elif val == '</s>':
            if object_output:
                doc.append({'sentence': doc_sent, 'metadata': metadata})
                doc_sent = []
            metadata = ''
            ns += 1
        elif val == '<S/>':
            pass
        else:
            attribs = parse_attribs(match.group(2))
            val = match.group(3)
            actual_val = ['']
            idx_of_token = index_of(para, val, idx, actual_val)
            if idx_of_token == -1:
                print('Warning: Cannot compute token index. Token: "{}" Text: "{}"'.format(val, para))
            idx = max(idx, idx_of_token + len(actual_val[0]))
            idx_of_token += 1
            nt += 1

            lemma = unescape_xml_chars(attribs.get('lemma', '_'))
            xpos = attribs.get('xpos', '_')
            upos = attribs.get('upos', '_')
            if idx < len(para) and not para_concat[idx].isspace():
                space_after = 'SpaceAfter=No'
            else:
                space_after = '_'

            if object_output:
                tok = {'id': tuple([nt]), 'text': actual_val[0], 'lemma': lemma, 'xpos': xpos, 'upos': upos, 'misc': space_after}
                doc_sent.append(tok)
            else:
                line = str(nt) + '\t{}\t{}\t{}\t{}\t_\t_\t_\t_\t{}\n'.format(actual_val[0], lemma,
                                                            upos, xpos, space_after)
                os.write(line)
            has_output = True

    if has_output and not object_output:
        os.write('\n')

    if object_output:
        return doc
    return


def process_tei(para, np, os, tei_root):
    if para.startswith(u"\uFEFF"):
        para = para[1:]

    tokens = tokenize(para)

    parent_map = {}

    id_prefix = 'F'
    parent_node = tei_root.find('text')
    node = ET.Element('p')
    parent_node.append(node)
    #node.set('xml:id', id_prefix + str(np))
    node.attrib['{http://www.w3.org/XML/1998/namespace}id'] = id_prefix + str(np)
    parent_map[parent_node] = node

    org_text = preprocess_tokens(tokens)

    idx = 0
    ns = 1
    nt = 0
    for match in token_regex.finditer(tokens):
        val = match.group()
        if val == '<s>':
            nt = 0
            node = ET.Element('s')
            #node.set('xml:id', id_prefix + str(np) + '.' + str(ns))
            node.attrib['{http://www.w3.org/XML/1998/namespace}id'] = id_prefix + str(np) + '.' + str(ns)
            parent_node.append(node)
            parent_map[node] = parent_node
            parent_node = parent_node[-1]
        elif val == '</s>':
            parent_node = parent_map[parent_node]
            ns += 1
        elif val == '<S/>':
            node = ET.Element('c')
            node.text = ' '
            parent_node.append(node)
            parent_map[node] = parent_node
        else:
            attribs = parse_attribs(match.group(2))
            val = match.group(3)
            actual_val = ['']
            idx_of_token = index_of(para, val, idx, actual_val)
            if (idx_of_token == -1):
                print('Warning: cannot compute token index. Token: "{}" Text "{}"'.format(val, para))
            idx = max(idx, idx_of_token + len(actual_val[0]))
            idx_of_token += 1
            nt += 1
            if match.group(1).startswith('c'):
                tag_name = 'pc'
            else:
                tag_name = 'w'
            node = ET.Element(tag_name)
            node.text = actual_val[0]
            #node.set('xml:id', id_prefix + str(np) + '.' + str(ns) + '.t' + str(nt))
            node.attrib['{http://www.w3.org/XML/1998/namespace}id'] = id_prefix + str(np) + '.' + str(ns) + '.t' + str(nt)

            lemma = attribs.get('lemma', None)
            xpos = attribs.get('xpos', None)
            upos = attribs.get('upos', None)
            if lemma:
                node.attrib['lemma'] = lemma
            if xpos:
                node.attrib['ana'] = 'mte:' + xpos
            if upos:
                node.attrib['msd'] = 'UposTag=' + upos

            parent_node.append(node)
            parent_map[node] = parent_node


def parse_attribs(val):
    res = dict()
    for token in re.findall(r'\w+=\"[^\"]*\"', val):
        key, val = token.split('=', 1)
        if val[0] != '"' or val[-1] != '"':
            raise Exception('Attrib value needs to be in double quotes.')
        res[key] = val[1:-1]
    return res


def process_text(text, os, tei_root, conllu, pass_newdoc_id, object_output=False):
    np = 0
    if object_output:
        document = []
    for line in text:
        if line.isspace() or line == '':
            continue
        line = line.replace('\n', '')

        # Normalize exotic characters
        line = normalize(line)

        if conllu:
            if object_output:
                pre_metadata = ''
            if pass_newdoc_id and line.startswith('# newdoc id = '):
                np = 0
                if object_output:
                    pre_metadata += line + '\n'
                else:
                    os.write(line)
                    os.write('\n')
            np += 1
            out = process_conllu(line, np, os, object_output=object_output)
            if object_output:
                if pre_metadata and len(out) > 0:
                    out[0]['metadata'] = pre_metadata + out[0]['metadata']
                document.append(out)
        elif tei_root is not None:
            np += 1
            process_tei(line, np, os, tei_root)
        else:
            np += 1
            process_tokenize_only(line, np, os)

    if object_output:
        return document
    return None


def normalize(text):
    text = text.replace('\xad', '-')   # Soft hyphens
    return text


def run(text=None, in_file=None, in_files=None, out_file=None, to_stdout=False, tei=False, conllu=False, pass_newdoc_id=False, object_output=False):
    """
    Run Obeliks on specified input.

    Reads input from 'text' parameter, or from files passed via 'in_file' or 'in_files'. If none of these three 
    parameters are supplied, input is read from stdin. The output gets written to the path specified inside
    'out_file' or to stdout if 'to_stdout' is True. If 'out_file' is None and 'to_stdout is False, return output
    as a string.

    Args:
        text: A string containing input text.
        in_file: Path to file with input text.
        in_files: List of files with input text.
        out_file: Path where the output gets written to.
        to_stdout: Write output to stdout. Has priority over 'out_file'.
        tei: Output in XML-TEI format.
        conllu: Output in CoNLL-U format.
        pass_newdoc_id: Pass lines starting with \"# newdoc id =\" to output. Only applies if CoNLL-U output is 
                        selected.
    """
    os = StringIO()
    if object_output:
        os = {}
        conllu = True
        tei = False
    elif to_stdout:
        os = sys.stdout
    elif out_file is not None:
        os = open(out_file, 'w', encoding='utf-8')

    if in_files and len(in_files) > 0:
        text = []
        for file_name in in_files:
            with open(file_name, encoding='utf-8') as f:
                text += f.readlines()
    elif in_file is not None:
        with open(in_file, encoding='utf-8') as f:
            text = f.readlines()
    elif text:
        text = text.splitlines()
    else:
        text = sys.stdin.readlines()

    if tei:
        tei_tree = create_tei_tree()
        out = process_text(text, os, tei_tree.getroot(), False, False)
        if isinstance(os, StringIO):
            return ET.tostring(tei_tree, encoding='utf8', method='xml')
        else:
            tei_tree.write(os.buffer, encoding='utf-8', xml_declaration=True, pretty_print=True)
    else:
        out = process_text(text, os, None, conllu, pass_newdoc_id, object_output=object_output)
    
    if isinstance(os, StringIO):
        contents = os.getvalue()
        os.close()
        return contents

    if not object_output and os is not sys.stdout:
        os.close()

    return out

