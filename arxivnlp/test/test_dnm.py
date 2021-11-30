import unittest
from arxivnlp.data.dnm import Dnm, DnmConfig
from lxml import etree
import os
import io


class TestDnm(unittest.TestCase):
    def test_simple(self):
        source = os.path.join(os.path.dirname(__file__),'resources','test_simple.html')
        tree = etree.parse(source)
        doc = Dnm(tree, dnm_config=DnmConfig(nodes_to_skip={'head'}, classes_to_skip={'ltx_para'}))
        print(doc.tokens)
        doc.tokens[3].insert_node(node=etree.XML('<span> hello world </span>'),pos=3)
        newHTML = etree.tostring(tree.getroot())
        print(' ')
        print(newHTML)

    def test_insert(self):
        html = '<a>abc<b>hgj</b>nope<c></c></a>'
        tree = etree.parse(io.StringIO(html))
        dnm = Dnm(tree, dnm_config=DnmConfig(nodes_to_skip=set(), classes_to_skip=set()))
        dnm.tokens[0].insert_node(node=etree.XML('<d></d>'),pos=2)
        dnm.tokens[2].insert_node(node=etree.XML('<e></e>'),pos=2)
        newHTML = etree.tostring(tree.getroot())
        self.assertEqual(newHTML, b'<a>ab<d/>c<b>hgj</b>no<e/>pe<c/></a>')
