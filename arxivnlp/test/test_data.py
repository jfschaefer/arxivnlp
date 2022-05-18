import copy
import unittest
from pathlib import Path

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

    def test_open_doc(self):
        config = copy.copy(Config.get())
        config.arxmliv_dir = Path(__file__).parent / 'resources' / 'arxmliv_test_dir'
        docs = ArXMLivDocs(config)

        def just_open(arxivid):
            with docs.open(arxivid) as _:
                pass

        just_open('1701.39125')
        just_open('1603.13523')         # in zip file
        just_open('cond-mat9401234')
        self.assertRaises(MissingDataException, lambda: just_open('1701.12345'))
        self.assertRaises(MissingDataException, lambda: just_open('1603.12345'))  # in zip file
        self.assertRaises(MissingDataException, lambda: just_open('9001.12345'))  # no such folder exists
        self.assertRaises(BadArxivId, lambda: just_open('bad'))
