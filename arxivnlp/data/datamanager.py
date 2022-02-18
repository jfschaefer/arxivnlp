from typing import Optional, Any, IO
from lxml import etree

from .arxivcategories import ArxivCategories
from .arxmlivdocs import ArXMLivDocs
from .dnm import DnmConfig, Dnm, DEFAULT_DNM_CONFIG
from ..config import Config


class DataManager(object):
    def __init__(self, config: Optional[Config] = None):
        if config:
            self.config = config
        else:
            self.config = Config.get()
        self.arxiv_categories = ArxivCategories(self.config)
        self.arxmliv_docs = ArXMLivDocs(self.config)

    html_parser: Any = etree.HTMLParser()    # Setting type to Any suppress annoying warnings

    def load_dnm(self, arxiv_id: str, dnm_config: Optional[DnmConfig] = None) -> Dnm:
        if dnm_config is None:
            dnm_config = DEFAULT_DNM_CONFIG
        with self.arxmliv_docs.open(arxiv_id) as fp:
            tree = etree.parse(fp, self.html_parser)
        return Dnm(tree, dnm_config)
