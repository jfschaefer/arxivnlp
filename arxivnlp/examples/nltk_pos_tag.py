import argparse
import nltk
from lxml import etree

import args
from arxivnlp.data.datamanager import DataManager
from arxivnlp.sentence_tokenize import sentence_tokenize
from arxivnlp.word_tokenize import word_tokenize

parser = argparse.ArgumentParser(description='Add NLTK-generated POS tags to arxiv documents', add_help=True)
parser.add_argument('arxivid', nargs='?', default='1608.05603')
arguments = args.parse_and_process(parser)
arxivid = arguments.arxivid

data_manager = DataManager()
dnm = data_manager.load_dnm(arxivid)

with open('1608.05390.txt', 'w') as f:
    f.write(dnm.string)
sentences = sentence_tokenize(dnm.get_full_substring())
with open('sentences.txt', 'w') as f:
    for s in sentences:
        f.write(repr(s))
        f.write('\n')

for s in sentences[::-1]:
    dnm.insert_node(node=etree.XML('<span style="color:red; font-size:150%">]</span>'), pos=s.backrefs[-1] + 1)
    words = word_tokenize(s)
    string_list = [word.string for word in words]
    tags = [pair[1] for pair in nltk.pos_tag(string_list)]
    tagged_words = list(zip(words, tags))
    for word, tag in tagged_words[::-1]:
        dnm.insert_node(node=etree.XML(f'<sup style="color:blue">{tag}</sup>'),
                        pos=word.backrefs[-1] + 1)
        dnm.insert_node(node=etree.XML('<span style="color:orange; font-size:120%">]</span>'),
                        pos=word.backrefs[-1] + 1)
        dnm.insert_node(node=etree.XML('<span style="color:orange; font-size:120%">[</span>'),
                        pos=word.backrefs[0])
    dnm.insert_node(node=etree.XML('<span style="color:red; font-size:150%">[</span>'), pos=s.backrefs[0])
dnm.tree.write('1608.05390-new.html')
