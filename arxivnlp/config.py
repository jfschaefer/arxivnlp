import configparser
import dataclasses
import logging
import os
import sys
from pathlib import Path
from typing import Optional


def str_to_path_if_not_none(path: Optional[str]) -> Optional[Path]:
    return Path(path) if path else None


class MissingConfigException(Exception):
    pass


@dataclasses.dataclass
class Config(object):
    _default_config: Optional['Config'] = None
    config_file: Optional[Path] = None
    arxmliv_dir: Optional[Path] = None
    other_data_dir: Optional[Path] = None
    cache_dir: Optional[Path] = None
    results_dir: Optional[Path] = None

    @classmethod
    def from_file(cls, file_path: Path) -> 'Config':
        parser = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        parser.read(file_path)
        config = Config()
        config.config_file = file_path
        to_path = str_to_path_if_not_none
        if 'DATA' in parser:
            config.arxmliv_dir = to_path(parser['DATA'].get('ArXMLivDir'))
            config.other_data_dir = to_path(parser['DATA'].get('OtherDataDir'))
            config.cache_dir = to_path(parser['DATA'].get('CacheDir'))
            config.results_dir = to_path(parser['DATA'].get('ResultsDir'))
        return config

    @classmethod
    def get(cls) -> 'Config':
        if cls._default_config is not None:
            return cls._default_config
        logger = logging.getLogger(__name__)
        if cls.config_file is not None:
            if not cls.config_file:
                raise MissingConfigException(f'File "{cls.config_file}" does not exist.')
            logger.info(f'Loading config from {cls.config_file}')
            return Config.from_file(cls.config_file)
        # possible locations for config files
        options = [Path('arxivnlp.conf'), Path('.arxivnlp.conf'),
                   Path('~/arxivnlp.conf'), Path('~/.arxivnlp.conf'), Path('~/.config/arxivnlp.conf')]
        for path in options:
            path = path.expanduser()
            if path.is_file():
                logger.info(f'Loading config from {path}')
                return Config.from_file(path)
        logger.warning(f'Failed to find a configuration file.')
        return Config()

    def set_as_default(self):
        Config._default_config = self


def configure(rootdir: Path, configfile=Path('~/.arxivnlp.conf')):
    import jinja2
    j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(Path(os.path.dirname(__file__)) / 'resources'))
    if configfile.is_file():
        print(f'Error: {str(configfile)} already exists.', file=sys.stderr)
        sys.exit(1)
    if not rootdir.is_dir():
        print(f'Creating {str(rootdir)}')
        rootdir.mkdir()
    with open(configfile, 'w') as fp:
        fp.write(j2_env.get_template('config-template.conf').render(root=str(rootdir)))
    print(f'Successfully created {str(configfile)}')


if __name__ == '__main__':
    def main():
        defaultrootdir = os.path.expanduser('~/arxivnlp')
        defaultconffile = os.path.expanduser('~/.arxivnlp.conf')
        import argparse
        parser = argparse.ArgumentParser(description='Create configuration file', add_help=True)
        parser.add_argument('--data-root', dest='rootdir', default=defaultrootdir,
                            help=f'Root directory for data (default: {defaultrootdir}')
        parser.add_argument('--file', dest='file', default=defaultconffile,
                            help=f'Name of the configuration file (default: {defaultconffile}, '
                                 'warning: might not be found if changed)')
        args = parser.parse_args()
        configure(Path(args.rootdir), Path(args.file))

    main()
