import unittest
from arxivnlp.data.document import Document
from lxml import etree
import os

class TestDocument(unittest.TestCase):
    def test_simple(self):
        source = os.path.join(os.path.dirname(__file__),'resources','test_simple.html')
        tree = etree.parse(source)
        doc = Document(tree, skipped_nodes=['head'])
        print(doc.stream)
