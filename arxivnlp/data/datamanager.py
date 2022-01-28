import re
from pathlib import Path
from typing import Optional
from lxml import etree

from .arxivcategories import ArxivCategories
from .dnm import DnmConfig, Dnm, DEFAULT_DNM_CONFIG
from .exceptions import BadArxivId, MissingDataException
from ..config import Config


class DataManager(object):
    def __init__(self, config: Optional[Config] = None):
        if config:
            self.config = config
        else:
            self.config = Config.get()
        self.arxiv_categories = ArxivCategories(self.config)

    arxiv_id_regex = re.compile(r'[^0-9]*(?P<yymm>[0-9]{4}).*')

    def locate_doc(self, arxiv_id: str) -> Path:
        match = DataManager.arxiv_id_regex.match(arxiv_id)
        if not match:
            raise BadArxivId(f'Failed to infer yymm from arxiv id "{arxiv_id}"')
        yymm = match.group('yymm')
        directory = self.config.arxmliv_dir / yymm
        if not directory.is_dir():
            raise MissingDataException(f'No such directory: "{directory}"')
        if arxiv_id.endswith('.html'):
            filename = directory / arxiv_id
        else:
            filename = directory / f'{arxiv_id}.html'
        return filename

    html_parser = etree.HTMLParser()

    def load_dnm(self, arxiv_id: str, dnm_config: Optional[DnmConfig] = None) -> Dnm:
        file = self.locate_doc(arxiv_id)
        if dnm_config is None:
            dnm_config = DEFAULT_DNM_CONFIG
        tree = etree.parse(str(file), self.html_parser)
        return Dnm(tree, dnm_config)
