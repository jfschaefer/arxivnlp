import json
import logging
from pathlib import Path
from typing import Dict, List, IO

from . import utils
from .cached import CachedData
from ..config import Config


class ArxivCategories(object):
    def __init__(self, config: Config):
        self.config = config
        self._doc_to_cats: CachedData[Dict[str, List[str]]] = CachedData(self.config, 'doc_to_cats', 'arxiv_categories',
                                                                         'arxiv document-to-category data')
        self._cat_to_docs: CachedData[Dict[str, List[str]]] = CachedData(self.config, 'cat_to_docs', 'arxiv_categories',
                                                                         'arxiv category-to-document data')

    @property
    def doc_to_cats(self) -> Dict[str, List[str]]:
        if not self._doc_to_cats.ensured():
            self._load_from_original()
        return self._doc_to_cats.data

    @property
    def cat_to_docs(self) -> Dict[str, List[str]]:
        if not self._cat_to_docs.ensured():
            self._load_from_original()
        return self._cat_to_docs.data

    def _load_from_original(self):
        logger = logging.getLogger(__name__)
        path = utils.require_other_data(self.config, Path('categories.txt'))
        logger.info(f'Loading arxiv categories from {path}')
        count = 0
        self._doc_to_cats.data = {}
        self._cat_to_docs.data = {}
        with open(path) as fp:
            for line in fp:
                count += 1
                docid, cats = line.split(':')
                for cat in cats.strip().split(', '):
                    self._doc_to_cats.data.setdefault(docid, []).append(cat)
                    self._cat_to_docs.data.setdefault(cat, []).append(docid)

        self._doc_to_cats.write_to_cache()
        self._cat_to_docs.write_to_cache()


def update(metadatafile: Path, config: Config):
    logger = logging.getLogger(__name__)

    def actual(fp: IO):
        data: Dict[str, List[str]] = {}
        logger.info(f'Loading arxiv category data - this may take a moment')
        for line in fp:
            if not line:
                continue
            content = json.loads(line)
            data[content['id']] = content['categories'].split()
        logger.info(f'Found category data on {len(data)} documents')
        with open(config.other_data_dir / 'categories.txt', 'w') as fp:
            for doc in sorted(data):
                fp.write(f'{doc}: ' + ', '.join(data[doc]) + '\n')

    if metadatafile.name.endswith('.zip'):
        import zipfile
        with zipfile.ZipFile(metadatafile) as file:
            assert len(file.namelist()) == 1
            with file.open(file.namelist()[0]) as fp:
                actual(fp)
    else:
        with open(metadatafile) as fp:
            actual(fp)
