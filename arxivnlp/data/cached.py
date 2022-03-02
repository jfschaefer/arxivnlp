import gzip
import io
import logging
import pickle
import zipfile
from collections import deque
from pathlib import Path
from typing import TypeVar, Generic, Optional, Dict, Tuple, Deque, Set, IO, List

from arxivnlp.config import Config

T = TypeVar('T')


class CachedData(Generic[T]):
    def __init__(self, config: Config, name: str, dirname: Optional[str] = None, data_descr: str = 'data'):
        self.config = config
        self.name = name
        self.dirname = dirname
        self.data_descr = data_descr

        self.data: Optional[T] = None

    def _get_filepath(self) -> Path:
        path = self.config.cache_dir
        assert path is not None
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
        if self.config.cache_dir is None:
            logger.error(f'No cache directory is specified in the config')
            return False
        path = self._get_filepath()
        if path.is_file():
            with gzip.open(path, 'rb') as fp:
                self.data = pickle.load(fp)  # type: ignore
                logger.info(f'Successfully loaded {self.data_descr} from {path}')
                return True
        else:
            logger.info(f'Failed to load {self.data_descr} from cache ({path} does not exist)')
        return False

    def write_to_cache(self):
        logger = logging.getLogger(__name__)
        assert self.data is not None
        if self.config.cache_dir is None:
            logger.error(f'Failed to cache {self.data_descr}: no cache directory is specified in the config')
            return
        path = self._get_filepath()
        logger.info(f'Attempting to cache {self.data_descr} at {path}')
        if not path.parent.exists():
            logger.info(f'Creating {path.parent}')
            path.parent.mkdir(parents=True)
        with gzip.open(path, 'wb', compresslevel=3) as fp:
            pickle.dump(self.data, fp, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info(f'Successfully cached {self.data_descr} at {path}')


class OpenedZipFile(zipfile.ZipFile):
    expiry: int
    opened_files: List[IO]

    def __init__(self, filename: str, expiry: int):
        zipfile.ZipFile.__init__(self, filename)
        self.expiry = expiry
        self.opened_files = []

    def open(self, *args, **kwargs) -> IO:
        file = super().open(*args, **kwargs)
        self.opened_files.append(file)
        return file

    def clean(self):
        self.opened_files = [file for file in self.opened_files if not file.closed]


class ZipFileCache(object):
    def __init__(self, config: Config):
        # filename -> zipfile, expiry
        self.zipfiles: Dict[str, OpenedZipFile] = {}
        # (filename, expiry when entered (only delete if it hasn't been extended))
        self.zipfiledeque: Deque[Tuple[str, int]] = deque()
        # files currently open from zip file
        self.currently_open: Dict[zipfile.ZipFile, Set[io.FileIO]] = {}

        self.max_open: int = config.max_open_zip_files if config.max_open_zip_files else 50

        # statistics
        self.stat_requested: int = 0
        self.stat_successes: int = 0
        self.stat_pushed_because_open: int = 0

    def delete_old(self):
        while len(self.zipfiles) > self.max_open:
            name, expiry = self.zipfiledeque.popleft()
            ozf = self.zipfiles[name]
            ozf.clean()
            if ozf.expiry == expiry:
                if not ozf.opened_files:
                    self.zipfiles[name].close()
                    del self.zipfiles[name]
                else:
                    self.stat_pushed_because_open += 1
                    self.push_back(ozf, name)

    def push_back(self, ozf: OpenedZipFile, name: str):
        if ozf.expiry < self.zipfiledeque[-1][1]:
            ozf.expiry = self.zipfiledeque[-1][1] + 1
            self.zipfiledeque.append((name, ozf.expiry))

    def cleanup(self):
        old = self.zipfiledeque
        self.zipfiledeque = deque()
        for e in old:
            if self.zipfiles[e[0]].expiry == e[1]:
                self.zipfiledeque.append(e)

    def __getitem__(self, path: Path) -> zipfile.ZipFile:
        self.stat_requested += 1
        name = str(path.resolve())
        if name not in self.zipfiles:
            expiry = self.zipfiledeque[-1][1] + 1 if len(self.zipfiledeque) else 0
            ozf = OpenedZipFile(name, expiry=expiry)
            self.zipfiles[name] = ozf
            self.zipfiledeque.append((name, expiry))
            self.delete_old()
            return ozf
        else:
            self.stat_successes += 1
            ozf = self.zipfiles[name]
            self.push_back(ozf, name)
            if len(self.zipfiledeque) > 20 * self.max_open:
                self.cleanup()
            return ozf

    def close(self):
        logger = logging.getLogger(__name__)
        for zf in self.zipfiles.values():
            if zf.opened_files:
                logger.warning(f'{zf.filename} still has open files')
            zf.close()
        if self.stat_requested:
            logger.info(f'Closing ZipFileCache. Cache hits: {self.stat_successes}/{self.stat_requested}. '
                        f'Pushbacks because of open files: {self.stat_pushed_because_open}')
