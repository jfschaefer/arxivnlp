import dataclasses
import configparser
import logging
from pathlib import Path
from typing import Optional


class MissingConfigException(Exception):
    pass


@dataclasses.dataclass
class Config(object):
    arxmliv_dir: Optional[Path] = None
    other_data_dir: Optional[Path] = None
    cache_dir: Optional[Path] = None
    results_dir: Optional[Path] = None

    @classmethod
    def from_file(cls, file_path: Path) -> 'Config':
        parser = configparser.ConfigParser()
        parser.read(file_path)
        config = Config()
        if 'DATA' in parser:
            config.arxmliv_dir = parser['DATA'].get('ArXMLivDir')
            config.other_data_dir = Path(parser['DATA'].get('OtherDataDir'))
            config.cache_dir = Path(parser['DATA'].get('CacheDir'))
            config.results_dir = parser['DATA'].get('ResultsDir')
        return config

    @classmethod
    def get(cls) -> 'Config':
        logger = logging.getLogger(__name__)
        # possible locations for config files
        options = [Path('~/.arxivnlp.conf'), Path('~/arxivnlp.conf'), Path('~/.config/arxivnlp.conf')]
        for path in options:
            path = path.expanduser()
            if path.is_file():
                logger.info(f'Loading config from {path}')
                return Config.from_file(path)
        logger.warning(f'Failed to find a configuration file.')
        return Config()
