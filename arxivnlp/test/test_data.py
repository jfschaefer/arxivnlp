import unittest

from arxivnlp.config import Config
from arxivnlp.data.arxivcategories import ArxivCategories
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
