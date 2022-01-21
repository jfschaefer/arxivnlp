import os
import unittest

from lxml import etree

from arxivnlp.data.dnm import Dnm, DEFAULT_DNM_CONFIG
from arxivnlp.sentence_tokenize import sentence_tokenize
from arxivnlp.word_tokenize import word_tokenize


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
            print(word_tokenize(s))
            for word in word_tokenize(s)[::-1]:
                doc.insert_node(node=etree.XML('<span style="color:orange; font-size:120%">]</span>'),
                                pos=word.backrefs[-1] + 1)
                doc.insert_node(node=etree.XML('<span style="color:orange; font-size:120%">[</span>'),
                                pos=word.backrefs[0])
            doc.insert_node(node=etree.XML('<span style="color:red; font-size:150%">[</span>'), pos=s.backrefs[0])
        tree.write('1608.05390-new.html')
