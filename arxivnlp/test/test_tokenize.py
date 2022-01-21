import os
import unittest

from lxml import etree

from arxivnlp.data.dnm import Dnm, DEFAULT_DNM_CONFIG
from arxivnlp.sentence_tokenize import sentence_tokenize
from arxivnlp.word_tokenize import word_tokenize

import nltk


class TestDnm(unittest.TestCase):
    def test_tokenize(self):
        parser = etree.HTMLParser()
        source = os.path.join(os.path.dirname(__file__), 'resources', '1608.05390.html')
        tree = etree.parse(source, parser)
        doc = Dnm(tree, dnm_config=DEFAULT_DNM_CONFIG)
        with open('1608.05390.txt', 'w') as f:
            f.write(doc.string)
        sentences = sentence_tokenize(doc.get_full_substring())
        with open('sentences.txt', 'w') as f:
            for s in sentences:
                f.write(repr(s))
                f.write('\n')

        for s in sentences[::-1]:
            doc.insert_node(node=etree.XML('<span style="color:red; font-size:150%">]</span>'), pos=s.backrefs[-1] + 1)
            words = word_tokenize(s)
            string_list = [word.string for word in words]
            tags = [pair[1] for pair in nltk.pos_tag(string_list)]
            tagged_words = list(zip(words, tags))
            for word, tag in tagged_words[::-1]:
                doc.insert_node(node=etree.XML(f'<sup style="color:blue">{tag}</sup>'),
                                pos=word.backrefs[-1] + 1)
                doc.insert_node(node=etree.XML('<span style="color:orange; font-size:120%">]</span>'),
                                pos=word.backrefs[-1] + 1)
                doc.insert_node(node=etree.XML('<span style="color:orange; font-size:120%">[</span>'),
                                pos=word.backrefs[0])
            doc.insert_node(node=etree.XML('<span style="color:red; font-size:150%">[</span>'), pos=s.backrefs[0])
        tree.write('1608.05390-new.html')
