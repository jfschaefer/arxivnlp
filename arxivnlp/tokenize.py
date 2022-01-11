from typing import List
from lxml import etree
from arxivnlp.data.dnm import SubString, get_node_classes


def is_ref_node(node: etree.Element) -> bool:
    classes = get_node_classes(node)
    return 'ltx_ref' in classes or 'ltx_cite' in classes

def sentence_tokenize(substring: SubString) -> List[SubString]:
    sentences = []
    sent_start = 0
    for i in range(len(substring)):
        if substring.string[i] not in {'.','!','?'}:
            continue
        isdot = substring.string[i] == '.'
        if isdot and i+1 < len(substring) and substring.string[i+1].islower() :
            continue
        if isdot and 0 < i < len(substring)-1 and substring.string[i-1].isdigit() and substring.string[i+1].isdigit():
            continue
        if i+1 < len(substring) and substring.string[i+1] == '\xa0':    # followed by a non-breaking space
            continue
        if i + 1 < len(substring) and substring.string[i+1] in {',','.',':',';'}:     # "e.g., ", "word..."
            continue
        if i + 2 < len(substring) and substring.string[i+1].isspace() and is_ref_node(substring.get_node(i+2)):
            continue
        sentences.append(substring[sent_start:i+1].strip().normalize_spaces())
        sent_start = i+1
    return sentences