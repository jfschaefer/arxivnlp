import argparse
import sys
from pathlib import Path
from typing import List, Dict, Callable

import arxivnlp.args
import arxivnlp.data.arxivcategories as arxivcategories
from arxivnlp.config import Config

COMMANDS: Dict[str, Callable[[List[str]], None]] = {}


def register(name: str):
    def decorator(func):
        COMMANDS[name] = func
        return func

    return decorator


@register('update-arxiv-metadata')
def update_arxiv_metadata(arguments: List[str]):
    parser = argparse.ArgumentParser(description='Update the arxiv metadata', add_help=True)
    parser.add_argument('metadata', help='Download from https://www.kaggle.com/Cornell-University/arxiv')
    args = arxivnlp.args.auto(args=arguments, parser=parser)
    arxivcategories.update(Path(args.metadata), Config.get())


def print_help():
    print('arxivnlp management tool')
    print('Available commands:')
    for cmd in COMMANDS:
        print(f'    {cmd}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_help()
    elif sys.argv[1] in COMMANDS:
        COMMANDS[sys.argv[1]](sys.argv[2:])
    else:
        print_help()
