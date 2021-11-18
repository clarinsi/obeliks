import regex as re
from pathlib import Path


tag_regex = re.compile(r'\</?[^>]+\>')
abbrv_regex = re.compile(r'<w>(\p{L}+)<\/w><c>\.<\/c>')
endofsentence_regex = re.compile(r'^<[wc]>[\p{Lu}"»“‘\'0-9]$')
abbrvexcl_regex = re.compile(r'(?P<step><w>(?P<word>\p{L}+)<\/w><c>\.<\/c>(?P<tail><S\/>)?)(?P<ctx>(<\/[ps]>)|(<[wc]>.))')
abbrvother_regex = re.compile(r'(?P<step><w>(?P<word>\p{L}+)<\/w><c>\.<\/c>(?P<tail><S\/>)?)<[wc]>[:,;0-9\p{Ll}]')

def load_list(path):
    tokens = set()
    with open(path, 'r', encoding='utf-8') as f:
        for token in f:
            token = token.strip()
            if not token == '' and not token.startswith('#'):
                tokens.add(token)
    return tokens

res_path = Path(__file__).parent / 'res/'

abbrv_seq = load_list(res_path / 'ListOSeq.txt')
abbrv_seg_seq = load_list(res_path / 'ListOSegSeq.txt')
abbrv_no_seg_seq = load_list(res_path / 'ListONoSegSeq.txt')
abbrv_excl = load_list(res_path / 'ListOExcl.txt')
abbrv_excl_CS = load_list(res_path / 'ListOExclCS.txt')
abbrv_seg = load_list(res_path / 'ListOSeg.txt')
abbrv_all = load_list(res_path / 'ListOAll.txt')
abbrv_all_CS = load_list(res_path / 'ListOAllCS.txt')

abbrv_seq_len = set()
for abbrv in abbrv_seq:
    length = 0
    for c in abbrv:
        if c == '.':
            length += 1
    abbrv_seq_len.add(length)
abbrv_seq_len = list(abbrv_seq_len)
abbrv_seq_len.sort(reverse = True)


def empty_if_none(s):
    if s is None:
        return ''
    else:
        return s.strip()


def process_abbrv_seq(text, seq_len):
    idx = 0
    regex = re.compile(r'(?P<jump>(?P<step><w>\p{L}+</w><c>\.</c>(<S/>)?)(<w>\p{L}+</w><c>\.</c>(<S/>)?){' \
            + str(seq_len - 1) + r'})(?P<ctx>(</[ps]>)|(<[wc]>.))')

    sb = []
    while True:
        m = regex.search(text, idx)
        if not m:
            break
        sb.append(text[idx : m.start()])
        xml = empty_if_none(m.group('jump'))
        abbrv_lower = re.sub(tag_regex, '', xml).replace(' ', '').lower()
        if abbrv_lower in abbrv_seq:
            idx = m.start() + len(xml)
            xml = re.sub(abbrv_regex, r'<w>\1.</w>', xml)
            if endofsentence_regex.search(empty_if_none(m.group('ctx'))):
                if abbrv_lower in abbrv_seg_seq:
                    xml += '</s><s>'
                elif abbrv_lower in abbrv_no_seg_seq:
                    xml += '<!s/>'
        else:
            xml = empty_if_none(m.group('step'))
            idx = m.start() + len(xml)
        sb.append(xml)

    sb.append(text[idx:])
    return ''.join(sb)


def process_abbrv_excl(text):
    idx = 0
    sb = []
    while True:
        m = abbrvexcl_regex.search(text, idx)
        if not m:
            break
        sb.append(text[idx : m.start()])
        word = empty_if_none(m.group('word'))
        word_lower = word.lower()
        if len(word) == 1 or word_lower in abbrv_excl or word in abbrv_excl_CS:
            xml = '<w>' + word + '.</w>' + empty_if_none(m.group('tail'))
            idx = m.start() + len(empty_if_none(m.group('step')))
            if word_lower in abbrv_seg and endofsentence_regex.search(empty_if_none(m.group('ctx'))):
                xml += '</s><s>'
        else:
            xml = empty_if_none(m.group('step'))
            idx = m.start() + len(xml)
        sb.append(xml)

    sb.append(text[idx:])
    return ''.join(sb)


def process_abbrv_other(text):
    idx = 0
    sb = []
    while True:
        m = abbrvother_regex.search(text, idx)
        if not m:
            break
        sb.append(text[idx : m.start()])
        word = empty_if_none(m.group('word'))
        word_lower = word.lower()
        if word_lower in abbrv_all or word in abbrv_all_CS:
            xml = '<w>' + word + '.</w>' + empty_if_none(m.group('tail'))
            idx = m.start() + len(empty_if_none(m.group('step')))
        else:
            xml = empty_if_none(m.group('step'))
            idx = m.start() + len(xml)
        sb.append(xml)
   
    sb.append(text[idx:])
    return ''.join(sb)


def exec_rules(text, rules):
    for rule in rules:
        regex = rule[0]    # Compiled search regex pattern
        rhs = rule[1]      # Replacement string

        has_val = '$val' in rhs
        has_txt = '$txt' in rhs

        if not has_val and not has_txt:
            text = re.sub(regex, rhs, text)
        else:
            def repl_func(match):
                if has_val:
                    return rhs.replace('$val', match.group(0))
                if has_txt:
                    return rhs.replace('$txt', re.sub(tag_regex, '', match.group(0)))
            text = re.sub(regex, repl_func, text) 

    return text


def load_rules(path):
    rules = []
    split_regex = re.compile(r'^(?P<regex>.*)((--)|(==))\>(?P<rhs>.*)$')

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line.startswith('#') and len(line) > 0:
                #opt = 0
                opt = re.UNICODE | re.VERSION1
                if '-->' in line:
                   opt |= re.IGNORECASE 

                match = re.search(split_regex, line)
                if match:
                    regex = re.compile(empty_if_none(match.group('regex')), opt)
                    rhs = empty_if_none(match.group('rhs'))

                    rules.append((regex, rhs))
    return rules


TOK_RULES_1 = load_rules(res_path / 'TokRulesPart1.txt')
TOK_RULES_2 = load_rules(res_path / 'TokRulesPart2.txt')
TOK_RULES_3 = load_rules(res_path / 'TokRulesPart3.txt')

def tokenize(text):
    xml =  exec_rules(text, TOK_RULES_1)
    for seq_len in abbrv_seq_len:
        xml = process_abbrv_seq(xml, seq_len)
    xml = process_abbrv_excl(xml)
    xml = process_abbrv_other(xml)
    xml = exec_rules(xml, TOK_RULES_2)
    xml = xml.replace('<!s/>', '')
    xml = exec_rules(xml, TOK_RULES_3)

    return xml

