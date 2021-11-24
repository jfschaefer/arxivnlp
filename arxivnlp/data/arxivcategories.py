import logging
import json
from pathlib import Path
from typing import Optional, Dict, List
from ..config import Config
from . import utils


class ArxivCategories(object):
    _doc_to_cats: Optional[Dict[str, List[str]]] = None
    _cat_to_docs: Optional[Dict[str, List[str]]] = None

    def __init__(self, config: Config):
        self.config = config

    @property
    def doc_to_cats(self) -> Dict[str, List[str]]:
        if self._doc_to_cats is None:
            self.load()
        assert self._doc_to_cats
        return self._doc_to_cats

    @property
    def cat_to_docs(self) -> Dict[str, List[str]]:
        if self._cat_to_docs is None:
            self._cat_to_docs = {}
            for doc, cats in self.doc_to_cats.items():
                for cat in cats:
                    self._cat_to_docs.setdefault(cat, []).append(doc)
        return self._cat_to_docs

    def load(self):
        logger = logging.getLogger(__name__)
        logger.debug('Loading arxiv categories')

        cache_dir = utils.check_cache(self.config, Path('arxiv_categories'))
        if cache_dir is not None:
            logger.info(f'Loading arxiv categories from cache ({cache_dir})')
            if self._load_from_cache(cache_dir):
                return
        else:
            logger.info('No cache for arxiv categories found')
        self._load_from_original()

    def _load_from_cache(self, cache_dir: Path) -> bool:
        with open(cache_dir/'condensed.json', 'r') as fp:
            self._doc_to_cats = json.load(fp)
        self._generate_cats_to_doc()


    def _load_from_original(self):
        path = utils.require_other_data(self.config, Path('arxiv-metadata-oai-snapshot.json'))
        with open(path, 'r') as fp:
            for line in fp:
                if not line:
                    continue
                content = json.loads(line)
                pass

