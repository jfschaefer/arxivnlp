import unittest
from arxivnlp.data.dnm import Dnm, DnmConfig
from lxml import etree
import os
import io


class TestDnm(unittest.TestCase):
    def test_simple(self):
        parser = etree.HTMLParser()
        source = os.path.join(os.path.dirname(__file__),'resources','1608.05390.html')
        tree = etree.parse(source, parser)
        doc = Dnm(tree, dnm_config=DnmConfig(nodes_to_skip={'head'}, classes_to_skip=set()))
        print(doc.string)

    def test_insert(self):
        html = '<a>abc<b>hgj</b>nope<c></c></a>'
        tree = etree.parse(io.StringIO(html))
        dnm = Dnm(tree, dnm_config=DnmConfig(nodes_to_skip=set(), classes_to_skip=set()))
        self.assertEqual(dnm.string, 'abchgjnope')
        dnm.insert_node(node=etree.XML('<d></d>'),pos=2)
        dnm.insert_node(node=etree.XML('<e></e>'),pos=8)
        newHTML = etree.tostring(tree.getroot())
        self.assertEqual(newHTML, b'<a>ab<d/>c<b>hgj</b>no<e/>pe<c/></a>')

    def test_math_node(self):
        html = '<a>abc<math>this is math string</math>nope<c></c></a>'
        tree = etree.parse(io.StringIO(html))
        dnm = Dnm(tree, dnm_config=DnmConfig(nodes_to_skip=set(), classes_to_skip=set()))
        self.assertEqual(dnm.string, 'abcMathNodenope')
        dnm.insert_node(node=etree.XML('<d>Inserted</d>'), pos=5)
        newHTML = etree.tostring(tree.getroot())
        self.assertEqual(newHTML, b'<a>abc<d>Inserted</d><math>this is math string</math>nope<c/></a>')