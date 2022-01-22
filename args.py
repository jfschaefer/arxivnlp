import argparse
import logging
from pathlib import Path

import arxivnlp.config
from typing import Optional


class ArgumentHandler(object):
    log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR}

    def __init__(self, handle_logging: bool = True, handle_config_file: bool = True):
        self.handle_logging = handle_logging
        self.handle_config_file = handle_config_file

    def add_arguments(self, argument_parser: argparse.ArgumentParser):
        if self.handle_logging:
            argument_parser.add_argument('--log-file', nargs='?', default='/tmp/arxivnlp.log', dest='log_file')
            argument_parser.add_argument('--log-level', nargs='?', default='INFO', choices=self.log_levels.keys(),
                                         dest='log_level')
        if self.handle_config_file:
            argument_parser.add_argument('--config', nargs='?', dest='config_file')

    def handle_arguments(self, args: argparse.Namespace):
        if self.handle_logging:
            logging.basicConfig(filename=args.log_file, filemode='w',
                                format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                                level=self.log_levels[args.log_level])
        if self.handle_config_file:
            if args.config_file:
                arxivnlp.config.Config.config_file = Path(args.config_file)


def parse_and_process(parser: argparse.ArgumentParser, handler: Optional[ArgumentHandler] = None) -> argparse.Namespace:
    if handler is None:
        handler = ArgumentHandler()
    handler.add_arguments(parser)
    args = parser.parse_args()
    handler.handle_arguments(args)
    return args


def auto():
    parser = argparse.ArgumentParser(description='An arxivnlp application', add_help=True)
    parse_and_process(parser)
