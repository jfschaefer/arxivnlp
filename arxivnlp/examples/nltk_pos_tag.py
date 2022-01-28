import argparse
import nltk

from arxivnlp import args
from arxivnlp.data.datamanager import DataManager
from arxivnlp.html_mark import highlight_dnmstring
from arxivnlp.sentence_tokenize import sentence_tokenize
from arxivnlp.word_tokenize import word_tokenize

parser = argparse.ArgumentParser(description='Add NLTK-generated POS tags to arxiv documents', add_help=True)
parser.add_argument('arxivid', nargs='?', default='1608.05390')
arguments = args.parse_and_process(parser)
arxivid = arguments.arxivid

data_manager = DataManager()
dnm = data_manager.load_dnm(arxivid)

sentences = sentence_tokenize(dnm.get_full_dnmstr())

for s in sentences:
    highlight_dnmstring(dnmstring=s, fontscale=1.5)
    words = word_tokenize(s)
    string_list = [word.string for word in words]
    tags = [pair[1] for pair in nltk.pos_tag(string_list)]
    for word, tag in zip(words, tags):
        highlight_dnmstring(dnmstring=word, color='orange', fontscale=1.2, tag=tag)
dnm.insert_added_nodes()
dnm.tree.write(f'{arxivid}-tagged.html')
