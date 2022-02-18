import argparse
import logging
import sys
from pathlib import Path

import arxivnlp.config
from typing import Optional, List, Any, Dict


class ArgumentHandler(object):
    log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR}

    def __init__(self, handle_logging: bool = True, handle_config_file: bool = True):
        self.handle_logging = handle_logging
        self.handle_config_file = handle_config_file

    def add_arguments(self, argument_parser: argparse.ArgumentParser):
        if self.handle_logging:
            argument_parser.add_argument('--log-file', nargs='?', default='stdout', dest='log_file',
                                         help='Specify the log file (or stdout/stderr)')
            argument_parser.add_argument('--log-level', nargs='?', default='INFO', choices=self.log_levels.keys(),
                                         dest='log_level')
        if self.handle_config_file:
            argument_parser.add_argument('--config', nargs='?', dest='config_file')

    def handle_arguments(self, args: argparse.Namespace):
        if self.handle_logging:
            logging_config: Dict[str, Any] = {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'level': self.log_levels[args.log_level]
            }
            if args.log_file not in {'stdout', 'stderr'}:
                logging_config['filename'] = args.log_file
                logging_config['filemode'] = 'w'
            else:
                logging_config['stream'] = {'stdout': sys.stdout, 'stderr': sys.stderr}[args.log_file]
            logging.basicConfig(**logging_config)

        if self.handle_config_file:
            if args.config_file:
                arxivnlp.config.Config.config_file = Path(args.config_file)
                arxivnlp.config.Config.get().set_as_default()


def parse_and_process(parser: argparse.ArgumentParser, handler: Optional[ArgumentHandler] = None,
                      args: Optional[List[str]] = None) -> argparse.Namespace:
    if handler is None:
        handler = ArgumentHandler()
    handler.add_arguments(parser)
    args = parser.parse_args(args=args)
    handler.handle_arguments(args)
    return args


def auto(args: Optional[List[str]] = None, parser: Optional[argparse.ArgumentParser] = None) -> argparse.Namespace:
    if parser is None:
        parser = argparse.ArgumentParser(description='An arxivnlp application', add_help=True)
    return parse_and_process(parser=parser, args=args)
