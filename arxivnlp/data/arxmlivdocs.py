import zipfile
from contextlib import contextmanager
from pathlib import Path
import re
from typing import IO, List

from ..config import Config
from .exceptions import BadArxivId, MissingDataException


class ArXMLivDocs(object):
    def __init__(self, config: Config):
        self.config = config

    arxiv_id_regex = re.compile(r'[^0-9]*(?P<yymm>[0-9]{4}).*')

    @contextmanager
    def open(self, arxiv_id: str) -> IO:
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
        if not b.is_dir():
            raise MissingDataException(f'{b} does not exist - make sure your config for the arXMLiv directory is set '
                                       f'correctly')
        # option 1: plain html files exist
        for path in [b/filename, b/'data'/filename, b/yymm/filename, b/'data'/yymm/filename]:
            attempts.append(path)
            if path.is_file():
                file = open(path)
                try:
                    found = True
                    yield file
                finally:
                    file.close()

        # option 2: it's in a zip file
        for path in [b/f'{yymm}.zip', b/'data'/f'{yymm}.zip']:
            attempts.append(path)
            if path.is_file():
                file_zip = zipfile.ZipFile(path)
                name = Path(yymm)/filename
                try:
                    actual_file = file_zip.open(str(name))
                    try:
                        found = True
                        yield actual_file
                    finally:
                        actual_file.close()
                except KeyError as e:
                    missing = MissingDataException(f'Failed to find {name} in {path}: {e}')
                    missing.__suppress_context__ = True
                    raise missing
                finally:
                    file_zip.close()

        if not found:
            raise MissingDataException(f'Failed to locate {arxiv_id} after looking in the following places:\n' +
                                       '\n'.join(f' * {a}' for a in attempts))
