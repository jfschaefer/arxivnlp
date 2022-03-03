import io
import itertools
import logging
import re
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import IO, List, Set, Optional, Iterator, Dict

from .cached import ZipFileCache, CachedData
from .exceptions import BadArxivId, MissingDataException
from ..config import Config


class ArXMLivDocs(object):
    def __init__(self, config: Config, zipfile_cache: Optional[ZipFileCache] = None):
        self.config = config
        self.zipfile_cache = zipfile_cache
        if self.zipfile_cache is None:
            logger = logging.getLogger()
            logger.warning('No ZipFileCache was provided - this might significantly slow down the opening of files')
        self.list_of_arxiv_ids: CachedData[List[str]] = \
            CachedData(self.config, 'arxiv-ids', data_descr='list of arxiv ids')
        self.arxivid_by_severity: CachedData[Dict[str, Set[str]]] = \
            CachedData(self.config, 'arxivid-by-severity', data_descr='latexml errors for arXMLiv documents')

    arxiv_id_regex = re.compile(r'[^0-9]*(?P<yymm>[0-9]{4}).*')

    @contextmanager
    def open(self, arxiv_id: str, read_as_text: bool = True) -> Iterator[IO]:
        if arxiv_id.endswith('.html'):
            arxiv_id = arxiv_id[:-5]
        match = ArXMLivDocs.arxiv_id_regex.match(arxiv_id)
        if not match:
            raise BadArxivId(f'Failed to infer yymm from arxiv id "{arxiv_id}"')
        yymm = match.group('yymm')
        filename = arxiv_id + '.html'

        # Go throught different directory structure options
        attempts: List[Path] = []
        found: bool = False
        b = self.config.arxmliv_dir
        if b is None:
            raise MissingDataException(f'Path to arXMLiv not specified in config')
        if not b.is_dir():
            raise MissingDataException(f'{b} does not exist - make sure your config for the arXMLiv directory is set '
                                       f'correctly')
        # option 1: plain html files exist
        for path in [b / filename, b / 'data' / filename, b / yymm / filename, b / 'data' / yymm / filename]:
            attempts.append(path)
            if path.is_file():
                file = open(path, 'r' if read_as_text else 'rb')
                try:
                    found = True
                    yield file
                finally:
                    file.close()

        # option 2: it's in a zip file
        for path in [b / f'{yymm}.zip', b / 'data' / f'{yymm}.zip']:
            attempts.append(path)
            if path.is_file():
                file_zip = self.zipfile_cache[path] if self.zipfile_cache is not None else zipfile.ZipFile(str(path))
                name = Path(yymm) / filename
                try:
                    actual_file = file_zip.open(str(name), 'r')
                except KeyError as e:
                    missing = MissingDataException(f'Failed to find {name} in {path}: {e}')
                    missing.__suppress_context__ = True
                    raise missing
                try:
                    found = True
                    result: IO
                    if read_as_text:
                        result = io.TextIOWrapper(actual_file, encoding='utf-8')
                    else:
                        result = actual_file
                    yield result
                finally:
                    actual_file.close()

        if not found:
            raise MissingDataException(f'Failed to locate {arxiv_id} after looking in the following places:\n' +
                                       '\n'.join(f' * {a}' for a in attempts))

    def arxiv_ids(self) -> List[str]:
        if self.list_of_arxiv_ids.ensured():
            assert self.list_of_arxiv_ids.data
            return self.list_of_arxiv_ids.data
        self.list_of_arxiv_ids.data = []
        yymm_regex = re.compile(r'^[0-9][0-9][0-9][0-9](\.zip)?$')
        processed_yymm: Set[str] = set()
        if self.config.arxmliv_dir is None:
            raise MissingDataException(f'ArXMLiv directory not specified in config')
        for path in itertools.chain(self.config.arxmliv_dir.iterdir(), (self.config.arxmliv_dir / 'data').iterdir()):
            if not yymm_regex.match(path.name):
                continue
            yymm = path.name[:4]
            if yymm in processed_yymm:
                continue
            processed_yymm.add(yymm)
            if path.name.endswith('.zip'):
                file_zip = self.zipfile_cache[path] if self.zipfile_cache is not None else zipfile.ZipFile(str(path))
                for name in file_zip.namelist():
                    if name.endswith('.html'):
                        self.list_of_arxiv_ids.data.append(name.split('/')[-1][:-5])
            elif path.is_dir():
                for filename in path.iterdir():
                    if filename.name.endswith('.html'):
                        self.list_of_arxiv_ids.data.append(filename.name[:-5])
        self.list_of_arxiv_ids.write_to_cache()
        return self.list_of_arxiv_ids.data

    def arxiv_id_to_severity(self, arxivid: str) -> str:
        def actual() -> str:
            assert self.arxivid_by_severity.data
            for k in self.arxivid_by_severity.data:
                if arxivid in self.arxivid_by_severity.data[k]:
                    return k
            raise Exception(f'No severity data for {arxivid}')

        if self.arxivid_by_severity.ensured():
            return actual()
        if self.config.arxmliv_dir is None:
            raise MissingDataException(f'ArXMLiv directory not specified in config')
        self.arxivid_by_severity.data = {}
        for level in ['no-problem', 'warning', 'error']:
            path = self.config.arxmliv_dir / 'meta' / 'grouped_by_severity.zip'
            if not path.is_file():
                raise MissingDataException(f'No such file {path}')
            file_zip = self.zipfile_cache[path] if self.zipfile_cache is not None else zipfile.ZipFile(str(path))
            self.arxivid_by_severity.data[level] = set()
            with io.TextIOWrapper(file_zip.open(f'{level}-tasks.txt'), encoding='utf-8') as fp:
                for line in fp:
                    line = line.strip()
                    if line:
                        assert line.endswith('.html')
                        self.arxivid_by_severity.data[level].add(line[:-5])
        self.arxivid_by_severity.write_to_cache()
        return actual()
