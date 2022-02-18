import unittest

from arxivnlp.config import Config
from arxivnlp.data.arxivcategories import ArxivCategories
from arxivnlp.data.arxmlivdocs import ArXMLivDocs
from arxivnlp.data.exceptions import MissingDataException, BadArxivId
from arxivnlp.test import utils


class TestData(unittest.TestCase):
    @utils.smart_skip(requires_data=True, is_slow=True)
    def test_arxivcats(self):
        config = Config.get()
        arxivcats = ArxivCategories(config)
        categories = arxivcats.doc_to_cats['0704.0009']
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0], 'astro-ph')
        categories = arxivcats.doc_to_cats['0704.0021']
        self.assertEqual(len(categories), 3)
        self.assertIn('physics.chem-ph', categories)
        docs = arxivcats.cat_to_docs['astro-ph']
        self.assertNotIn('0704.0021', docs)
        self.assertIn('0704.0009', docs)

    @utils.smart_skip(requires_data=True)
    def test_open_doc(self):
        docs = ArXMLivDocs(Config.get())

        def just_open(arxivid):
            with docs.open(arxivid) as _:
                pass

        just_open('1402.4845')
        just_open('cond-mat9407123')
        self.assertRaises(MissingDataException, lambda: just_open('1402.12345'))
        self.assertRaises(MissingDataException, lambda: just_open('9001.12345'))
        self.assertRaises(BadArxivId, lambda: just_open('bad'))
