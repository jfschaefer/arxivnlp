import multiprocessing
from pathlib import Path
from typing import Any, Tuple, List, Set

from lxml import etree

import arxivnlp.args
from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager
from arxivnlp.data.utils import require_other_data

arxivnlp.args.auto()
config = Config.get()

ltx_unit_list_path = require_other_data(config, Path('ltx_unit.txt'))

with open(ltx_unit_list_path, 'r') as fp:
    ltx_unit_arxivids = [line.strip() for line in fp.readlines() if line.strip()]

datamanager = DataManager(config)
html_parser: Any = etree.HTMLParser()  # Setting type to Any suppress annoying warnings


def get_description(arxivid: str) -> Tuple[str, str]:
    with datamanager.arxmliv_docs.open(arxivid) as fp:
        dom = etree.parse(fp, html_parser)
        xrefs: Set[str] = set()
        mis: Set[str] = set()
        for node in dom.xpath('//*[@class="ltx_unit"]'):
            if node.xpath('./@xref'):    # due to a bug in older latexml versions, xref is sometimes missing
                xrefs.add(node.xpath('./@xref')[0])
            if node.xpath('./text()'):   # apparently even this doesn't always exist (e.g. \watt\per\centimeter\square)
                mis.add(node.xpath('./text()')[0])
        csyms: Set[str] = set(dom.xpath('//csymbol/@id'))
        mrows = len(dom.xpath('//mrow[@class="ltx_unit"]'))
        return arxivid, f'{len(xrefs)},{len(mis)},{len(xrefs.intersection(csyms))},{mrows}'


results: List[Tuple[str, str]] = []
with multiprocessing.Pool(
        datamanager.config.number_of_processes if datamanager.config.number_of_processes else 1) as pool:
    for i, result in enumerate(pool.imap(get_description, ltx_unit_arxivids, chunksize=20)):
        print(f'{i:6d}/{len(ltx_unit_arxivids)}     {result}')
        results.append(result)

with open(config.other_data_dir / 'ltx_unit_sorted.txt', 'w') as fp:
    for result in results:
        fp.write(f'{result[0]},{result[1]}\n')
