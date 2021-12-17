import unittest
from arxivnlp.data.dnm import Dnm, DnmConfig, DEFAULT_DNM_CONFIG
from lxml import etree
from arxivnlp.tokenize import sentence_tokenize
import os
import io

class TestDnm(unittest.TestCase):
    def test_sentence_tokenize(self):
        parser = etree.HTMLParser()
        source = os.path.join(os.path.dirname(__file__),'resources','1608.07211.html')
        tree = etree.parse(source, parser)
        doc = Dnm(tree, dnm_config=DEFAULT_DNM_CONFIG)
        with open('1608.05390.txt','w') as f:
            f.write(doc.string)
        sentences = sentence_tokenize(doc.get_full_substring())
        with open('sentences.txt', 'w') as f:
            for s in sentences:
                f.write(repr(s))
                f.write('\n')