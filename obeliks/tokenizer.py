import sys
import regex as re
import lxml.etree as ET
from io import StringIO

from . rules import tokenize


amp_pattern = re.compile(r'&(amp;)?')
lt_pattern = re.compile(r'<|(&lt;)')
gt_pattern = re.compile(r'>|(&gt;)')


def create_tei_tree():
    root = ET.Element('TEI')
    root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
    #root.set('xml:lang', 'sl')
    attr = root.attrib
    attr['{http://www.w3.org/XML/1998/namespace}lang'] = "sl"
    root.append(ET.Element('text'))
    return ET.ElementTree(root)


def index_of(string, substring, from_idx, val):
    val[0] = ''
    pattern = None
    if substring == '&amp;':
        pattern = amp_pattern
    elif substring == '&lt;':
        pattern = lt_pattern
    elif substring == '&gt;':
        pattern = gt_pattern
   
    if pattern:
        for match in pattern.finditer(string):
            if match.start() < from_idx:
                continue
            elif match.start() >= from_idx:
                val[0] = match.group()
                return match.start()
        return -1
    val[0] = substring
    return string.find(substring, from_idx)


def preprocess_tokens(tokens):
    stoken_regex = re.compile(r'<s>.*?</s>')

    org_text = []
    for match in stoken_regex.finditer(tokens):
        val = match.group()
        val = val.replace('<s>', '')
        val = val.replace('</s>', '')
        val = val.replace('<w>', '')
        val = val.replace('</w>', '')
        val = val.replace('<c>', '')
        val = val.replace('</c>', '')
        val = val.replace('<S/>', ' ')
        val = val.replace(' {2,}', ' ')
        val = re.sub(' +', ' ', val)
        org_text.append(val.strip())

    return org_text

def process_tokenize_only(para, np, os):
    if para.startswith(u"\uFEFF"):
        para = para[1:]

    tokens = tokenize(para)
    org_text = preprocess_tokens(tokens)

    token_regex = re.compile(r'<S/>|</?s>|<([wc])>([^<]+)</[wc]>')
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
            val = match.group(2)
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



def process_conllu(para, np, os):
    if para.startswith(u"\uFEFF"):
        para = para[1:]

    para_concat = ''.join(para)

    tokens = tokenize(para)

    os.write('# newpar id = {}\n'.format(np))

    org_text = preprocess_tokens(tokens)

    token_regex = re.compile(r'<S/>|</?s>|<([wc])>([^<]+)</[wc]>')
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
            os.write('# sent_id = {}.{}\n'.format(np, ns))
            os.write('# text = {}\n'.format(org_text[ns - 1]))
        elif val == '</s>':
            ns += 1
        elif val == '<S/>':
            pass
        else:
            val = match.group(2)
            actual_val = ['']
            idx_of_token = index_of(para, val, idx, actual_val)
            if idx_of_token == -1:
                print('Warning: Cannot compute token index. Token: "{}" Text: "{}"'.format(val, para))
            idx = max(idx, idx_of_token + len(actual_val[0]))
            idx_of_token += 1
            nt += 1
            line = str(nt) + '\t{}\t_\t_\t_\t_\t_\t_\t_'.format(actual_val[0])
            if idx < len(para) and not para_concat[idx].isspace():
                space_after = 'SpaceAfter=No'
            else:
                space_after = '_'
            line += '\t{}\n'.format(space_after)
            os.write(line)
            has_output = True

    if has_output:
        os.write('\n')


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

    token_regex = re.compile(r'<S/>|</?s>|<([wc])>([^<]+)</[wc]>')
    idx = 0
    ns = 1
    nt = 0
    old_ns = 1
    has_output = False
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
            val = match.group(2)
            actual_val = ['']
            idx_of_token = index_of(para, val, idx, actual_val)
            if (idx_of_token == -1):
                print('Warning: cannot compute token index. Token: "{}" Text "{}"'.format(val, para))
            idx = max(idx, idx_of_token + len(actual_val[0]))
            idx_of_token += 1
            nt += 1
            if match.group(1) == 'c':
                tag_name = 'pc'
            else:
                tag_name = 'w'
            node = ET.Element(tag_name)
            node.text = actual_val[0]
            #node.set('xml:id', id_prefix + str(np) + '.' + str(ns) + '.t' + str(nt))
            node.attrib['{http://www.w3.org/XML/1998/namespace}id'] = id_prefix + str(np) + '.' + str(ns) + '.t' + str(nt)
            parent_node.append(node)
            parent_map[node] = parent_node


def process_text(text, os, tei_root, conllu, pass_newdoc_id):
    np = 0
    for line in text:
        if line.isspace() or line == '':
            continue

        # Normalize exotic characters
        line = normalize(line)

        if conllu:
            if pass_newdoc_id and line.startswith('# newdoc id = '):
                np = 0
                os.write(line)
                os.write('\n')
            np += 1
            process_conllu(line, np, os)
        elif tei_root is not None:
            np += 1
            process_tei(line, np, os, tei_root)
        else:
            np += 1
            process_tokenize_only(line, np, os)

def normalize(text):
    text = text.replace('\xad', '-')   # Soft hyphens
    return text


def run(text=None, in_file=None, in_files=None, out_file=None, to_stdout=False, tei=False, conllu=False, pass_newdoc_id=False):
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
    if to_stdout:
        os = sys.stdout
    elif out_file is not None:
        os = open(out_file, 'w', encoding = 'utf-8')

    if in_files and len(in_files) > 0:
        text = []
        for file_name in in_files:
            with open(file_name) as f:
                text += f.readlines()
    elif in_file is not None:
        with open(in_file) as f:
            text = f.readlines()
    elif text:
        text = text.splitlines()
    else:
        text = sys.stdin.readlines()

    if tei:
        tei_tree = create_tei_tree()
        process_text(text, os, tei_tree.getroot(), False, False)
        if isinstance(os, StringIO):
            return ET.tostring(tei_tree, encoding='utf8', method='xml')
        else:
            tei_tree.write(os.buffer, encoding='utf-8', xml_declaration=True, pretty_print=True)
    else:
        process_text(text, os, None, conllu, pass_newdoc_id)
    
    if isinstance(os, StringIO):
        contents = os.getvalue()
        os.close()
        return contents

    if os is not sys.stdout:
        os.close()

    return None

