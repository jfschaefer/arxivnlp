import gzip
import logging
import pickle
from pathlib import Path
from typing import TypeVar, Generic, Optional

from arxivnlp.config import Config

T = TypeVar('T')


class CachedData(Generic[T]):
    def __init__(self, config: Config, name: str, dirname: Optional[str] = None, data_descr: str = 'data'):
        self.config = config
        self.name = name
        self.dirname = dirname
        self.data_descr = data_descr

        self.data: Optional[T] = None

    def get_filepath(self) -> Path:
        path = self.config.cache_dir
        if self.dirname is not None:
            path = path / self.dirname
        return path / (self.name + '.dmp.gz')

    def ensured(self) -> bool:
        if self.data is None:
            return self.try_load_from_cache()
        return True

    def try_load_from_cache(self) -> bool:
        logger = logging.getLogger(__name__)
        logger.info(f'Attempting to load {self.data_descr} from cache')
        path = self.get_filepath()
        if path.is_file():
            with gzip.open(path, 'rb') as fp:
                self.data = pickle.load(fp)
                logger.info(f'Successfully loaded {self.data_descr} from {path}')
                return True
        else:
            logger.info(f'Failed to load {self.data_descr} from cache ({path} does not exist)')
        return False

    def write_to_cache(self):
        assert self.data is not None
        path = self.get_filepath()
        logger = logging.getLogger(__name__)
        logger.info(f'Attempting to cache {self.data_descr} at {path}')
        if not path.parent.exists():
            logger.info(f'Creating {path.parent}')
            path.parent.mkdir(parents=True)
        with gzip.open(path, 'wb', compresslevel=3) as fp:
            pickle.dump(self.data, fp, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info(f'Successfully cached {self.data_descr} at {path}')
