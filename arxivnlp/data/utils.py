from pathlib import Path
from typing import Optional

from arxivnlp.data.exceptions import MissingDataException
from arxivnlp.config import Config, MissingConfigException


def require_other_data(config: Config, rel_path: Path) -> Path:
    if config.other_data_dir is None:
        raise MissingConfigException('No directory for other data was specified in the configuration')
    path = config.other_data_dir / rel_path
    if not path.is_file():
        raise MissingDataException(f'No such file {path}')
    return path


def check_cache(config: Config, rel_path: Path) -> Optional[Path]:
    if config.cache_dir is None:
        return None
    path = config.cache_dir/rel_path
    return path if path.exists() else None
