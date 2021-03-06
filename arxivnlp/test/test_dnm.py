import io
import os
import unittest
from typing import Any

from lxml import etree

from arxivnlp.data.dnm import Dnm, DnmConfig, DEFAULT_DNM_CONFIG


class TestDnm(unittest.TestCase):
    def test_insert(self):
        html = '<a>abc<b>hgj</b>nope<c></c></a>'
        tree = etree.parse(io.StringIO(html))
        dnm = Dnm(tree, dnm_config=DnmConfig(nodes_to_skip=set(), classes_to_skip=set(), nodes_to_replace={},
                                             classes_to_replace={}))
        self.assertEqual(dnm.string, 'abchgjnope')
        dnm.add_node(node=etree.XML('<d></d>'), pos=2)
        dnm.add_node(node=etree.XML('<e></e>'), pos=8)
        dnm.insert_added_nodes()
        new_html = etree.tostring(tree.getroot())
        self.assertEqual(new_html, b'<a>ab<d/>c<b>hgj</b>no<e/>pe<c/></a>')

    def test_math_node(self):
        html = '<a>abc <math>this is math string</math> nope<c></c></a>'
        tree = etree.parse(io.StringIO(html))
        dnm = Dnm(tree, dnm_config=DnmConfig(nodes_to_skip=set(), classes_to_skip=set(),
                                             nodes_to_replace={'math': 'MathNode'},
                                             classes_to_replace={}))
        self.assertEqual(dnm.string, 'abc MathNode nope')
        self.assertEqual(dnm.backrefs_token[3].get_surrounding_node().tag, 'a')
        self.assertEqual(dnm.backrefs_token[12].get_surrounding_node().tag, 'a')
        substring = dnm.get_full_dnmstr()
        self.assertEqual(substring.string, 'abc MathNode nope')
        self.assertEqual(substring.get_node(3).tag, 'a')
        self.assertEqual(substring.get_node(12).tag, 'a')

        dnm.add_node(node=etree.XML('<d>Inserted</d>'), pos=6)
        dnm.insert_added_nodes()
        new_html = etree.tostring(tree.getroot())
        self.assertEqual(new_html, b'<a>abc <d>Inserted</d><math>this is math string</math> nope<c/></a>')
