import unittest
from arxivnlp.data.dnm import Dnm, DnmConfig
from lxml import etree
import os

class TestDnm(unittest.TestCase):
    def test_simple(self):
        source = os.path.join(os.path.dirname(__file__),'resources','test_simple.html')
        tree = etree.parse(source)
        doc = Dnm(tree, dnm_config=DnmConfig(nodes_to_skip={'head'}, classes_to_skip={'ltx_para'}))
        print(doc.stream)
