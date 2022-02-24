import argparse
import logging
import multiprocessing
from typing import Tuple

from arxivnlp.data import datamanager
from arxivnlp.args import auto
from arxivnlp.utils import StatusBar, StatusLine


class Status(StatusLine):
    def __init__(self, total_docs):
        StatusLine.__init__(self, 120)
        self.total_docs = total_docs
        self.processed_docs = 0
        self.found = 0
        self.status_bar = StatusBar(30, with_time=True)

    def update_string(self):
        self.status_bar.set(self.processed_docs / self.total_docs)
        self.string = f'{str(self.status_bar)}    {self.processed_docs}/{self.total_docs}, Found {self.found}'
        self.outdated = False


parser = argparse.ArgumentParser(description='Find all documents with a substring', add_help=True)
parser.add_argument('substring', help='Substring to find in documents')
parser.add_argument('outfile', help='File to store results in')
args = auto(parser=parser)

logger = logging.getLogger(__name__)
dm = datamanager.DataManager()
logger.info('Loading list of arXMLiv documents')
arxivids = dm.arxmliv_docs.arxiv_ids()
logger.info(f'Found {len(arxivids)} documents')

status = Status(len(arxivids))


def check(arxiv_id) -> Tuple[str, str]:
    try:
        with dm.arxmliv_docs.open(arxiv_id) as fp:
            s = fp.read()
        return ('found' if args.substring in s else 'notfound'), arxiv_id
    except Exception as e:
        return str(e), arxiv_id
    except UnicodeDecodeError as e:
        return str(e), arxiv_id


with open('/tmp/.arxivnlp.processed.txt', 'w') as pfp:
    with open(args.outfile, 'w') as f:
        with multiprocessing.Pool(dm.config.number_of_processes if dm.config.number_of_processes else 1) as pool:
            for i, result in enumerate(pool.imap(check, arxivids, chunksize=50)):
                result, doc_id = result
                if result == 'found':
                    f.write(f'{doc_id}\n')
                    status.found += 1
                elif result != 'notfound':
                    status.clear()
                    print('Error in ', doc_id)
                    print(result)
                pfp.write(f'{doc_id}\n')
                status.processed_docs += 1
                status.outdated = True
                if i % 10 == 0:
                    status.update()
