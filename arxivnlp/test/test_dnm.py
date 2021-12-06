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
        self.assertEqual(doc.string, '\n\n  \n    def\n  \n')

    def test_insert(self):
        html = '<a>abc<b>hgj</b>nope<c></c></a>'
        tree = etree.parse(io.StringIO(html))
        dnm = Dnm(tree, dnm_config=DnmConfig(nodes_to_skip=set(), classes_to_skip=set()))
        self.assertEqual(dnm.string, 'abchgjnope')
        dnm.insert_node(node=etree.XML('<d></d>'),pos=2)
        dnm.insert_node(node=etree.XML('<e></e>'),pos=8)
        newHTML = etree.tostring(tree.getroot())
        self.assertEqual(newHTML, b'<a>ab<d/>c<b>hgj</b>no<e/>pe<c/></a>')
