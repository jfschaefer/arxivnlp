from ..config import Config
from .arxivcategories import ArxivCategories


class DataManager(object):
    def __init__(self, config: Config):
        self.config = config
        self.arxive_categories = ArxivCategories(config)
