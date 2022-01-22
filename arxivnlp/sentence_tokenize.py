from typing import List, Optional

from lxml import etree

from arxivnlp.data.dnm import DnmStr, get_node_classes


def is_ref_node(node: etree.Element) -> bool:
    classes = get_node_classes(node)
    return 'ltx_ref' in classes or 'ltx_cite' in classes


def is_display_math(node: etree.Element) -> bool:
    classes = get_node_classes(node)
    return 'ltx_equation' in classes


def is_in_header(node: etree.Element) -> bool:
    if node.tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
        return True
    parent = node.getparent()
    if parent is not None and is_in_header(parent):
        return True
    return False


def sentence_tokenize(substring: DnmStr) -> List[DnmStr]:
    sentences = []
    sent_start = 0
    in_header = False
    for i in range(len(substring)):
        new_sent_start: Optional[int] = None
        if normal_end_of_sentence(substring, i):
            new_sent_start = i + 1
        if not in_header and is_in_header(substring.get_node(i)):
            in_header = True
            new_sent_start = i
        if in_header and not is_in_header(substring.get_node(i)):
            in_header = False
            new_sent_start = i
        if is_display_math(substring.get_node(i)) and not is_display_math(substring.get_node(i + 1)) and \
                substring.string[i + 1].isspace() and substring.string[i + 2].upper():
            new_sent_start = i + 1
        if new_sent_start is not None:
            new_sent = substring[sent_start:new_sent_start].strip().normalize_spaces()
            if len(new_sent) > 0:
                sentences.append(new_sent)
            sent_start = new_sent_start
    return sentences


def normal_end_of_sentence(substring: DnmStr, i: int) -> bool:
    if substring.string[i] not in {'.', '!', '?'}:
        return False
    isdot = substring.string[i] == '.'
    if isdot and i + 1 < len(substring) and substring.string[i + 1].islower():
        return False
    if (isdot and
            0 < i < len(substring) - 1 and
            substring.string[i - 1].isdigit() and
            substring.string[i + 1].isdigit()):
        return False
    if i + 1 < len(substring) and substring.string[i + 1] == '\xa0':  # followed by a non-breaking space
        return False
    if i + 1 < len(substring) and substring.string[i + 1] in {',', '.', ':', ';'}:  # "e.g., ", "word..."
        return False
    if i + 2 < len(substring) and substring.string[i + 1].isspace() and is_ref_node(substring.get_node(i + 2)):
        return False
    return True
