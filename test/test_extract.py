import unittest
import io

from lxml import etree

from arxivnlp import extract



class TestExtract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.htmlparser = etree.HTMLParser()


    def test_whitespace_normalization(self):
        html = '<html><body>\n\nabc  \n<br/>  def\n<a>ghi</a>jkl</body></html> '
        tree = etree.parse(io.StringIO(html), self.htmlparser)
        doc = extract.Document(tree, True)

        # before removing whitespace
        s = doc.getString()
        self.assertEqual(s, '\n\nabc  \n  def\nghijkl')
        oldbackrefs = {}
        for letter in 'abcdefghijkl':
            oldbackrefs[letter] = doc.backrefs[s.index(letter)]
        doc.cleanup_whitespace()

        # after removing whitespace
        s = doc.getString()
        self.assertEqual(doc.getString(), 'abc def ghijkl')
        for letter in 'abcdefghijkl':
            # backreferences shouldn't change
            self.assertEqual(oldbackrefs[letter], doc.backrefs[s.index(letter)])


    def test_node_insertion(self):
        # A: test insertion in text (tail) nodes, including that backrefs are updated appropriately for
        # further insertions
        html = '<html><body>abc<br/>def</body></html> '
        tree = etree.parse(io.StringIO(html), self.htmlparser)
        doc = extract.Document(tree, True)
        doc.cleanup_whitespace()
        self.assertEqual(doc.getString(), 'abcdef')

        doc.insert_node_at_offset(0, etree.XML('<b>X</b>'))
        doc.insert_node_at_offset(1, etree.XML('<b>X</b>'))
        doc.insert_node_at_offset(3, etree.XML('<b>X</b>'))
        doc.insert_node_at_offset(4, etree.XML('<b>X</b>'))

        
        newHtml = etree.tostring(tree.getroot())
        shouldBe = b'<html><body><b>X</b>a<b>X</b>bc<br/><b>X</b>d<b>X</b>ef</body></html>'
        self.assertEqual(newHtml, shouldBe)

        # B: test insertion into nodes
        html = '<html><body>ab<h1>cd</h1>e<h2/><math/></body></html>'
        tree = etree.parse(io.StringIO(html), self.htmlparser)
        doc = extract.Document(tree, True)
        doc.cleanup_whitespace()
        self.assertEqual(doc.getString(), 'ab @HEADER_START@cd@HEADER_END@ e @HEADER_START@@HEADER_END@ @FORMULA0@')

        # print()
        # print(doc.backrefs[10])
        doc.insert_node_at_offset(10, etree.XML('<b>S</b>'))
        doc.insert_node_at_offset(25, etree.XML('<b>E</b>'))
        doc.insert_node_at_offset(40, etree.XML('<b>s</b>'))
        doc.insert_node_at_offset(50, etree.XML('<b>e</b>'))
        doc.insert_node_at_offset(65, etree.XML('<b>N</b>'))

        newHtml = etree.tostring(tree.getroot())
        shouldBe = b'<html><body>ab<h1><b>S</b>cd<b>E</b></h1>e<h2><b>s</b><b>e</b></h2><b>N</b><math/></body></html>'
        self.assertEqual(newHtml, shouldBe)




if __name__ == '__main__':
    unittest.main()
