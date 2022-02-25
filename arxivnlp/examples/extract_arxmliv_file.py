import argparse
from pathlib import Path

import arxivnlp.args
from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager

parser = argparse.ArgumentParser(description='Extract arXMLiv file', add_help=True)
parser.add_argument('arxivid', help='arXiv-ID of the file')
parser.add_argument('target', help='Where to store the file')
args = arxivnlp.args.auto(parser=parser)
config = Config.get()

datamanager = DataManager(config)
path = Path(args.target)
if path.is_dir:
    path = path / f'{args.arxivid}.html'

with open(path, 'w') as fpout:
    with datamanager.arxmliv_docs.open(args.arxivid) as fpin:
        fpout.write(fpin.read())

print(f'Created {path.as_uri()}')
