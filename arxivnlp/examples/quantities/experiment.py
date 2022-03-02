from pathlib import Path
from typing import List, Any

from lxml import etree

import arxivnlp.args
from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager
from arxivnlp.data.utils import require_other_data
from arxivnlp.examples.quantities.wikidata import QuantityWikiDataLoader, QuantityWikiData


def get_relevant_documents(config: Config) -> List[str]:
    """ returns arxiv ids, sorted by how useful they are wrt ltx_unit """
    path = require_other_data(config, Path('ltx_unit_sorted.txt'))
    d = {}
    with open(path) as fp:
        for line in fp:
            if not line.strip():
                continue
            parts = line.strip().split(',')
            d[parts[0]] = float(parts[-2]) * float(parts[-3]) ** 0.5
            # d[parts[0]] = float(parts[-1])  # sort by count(//mrow[@class="ltx_unit"])
    print('TOTAL SCORE', sum(d.values()))
    return sorted((a for a in d), key=lambda a: -d[a])


def process(arxivid: str, data_manager: DataManager, data: QuantityWikiData):
    html_parser: Any = etree.HTMLParser()  # Setting type to Any suppress annoying warnings
    with data_manager.arxmliv_docs.open(arxivid) as fp:
        # TODO: Make this more interesting
        dom = etree.parse(fp, html_parser)
        for node in dom.xpath('//*[@class="ltx_unit"]'):
            if not node.xpath('./@xref'):
                print('skipping')
                continue
            xref = node.xpath('./@xref')[0]
            value = node.xpath(f'./ancestor::math//csymbol[@id="{xref}"]/text()')
            if not value:
                print('skipping')
                continue
            value = value[0]
            parent = node.getparent()
            while parent.tag != 'math':
                parent = parent.getparent()
            parent.addnext(etree.XML(f'<span style="color:red;font-weight:bold">{value}</span>'))
        with open(f'/tmp/units-{arxivid}.html', 'wb') as fp:
            fp.write(etree.tostring(dom))


def main():
    arxivnlp.args.auto()
    config = Config.get()
    data = QuantityWikiDataLoader(config).get()
    data_manager = DataManager(config)
    arxivids = get_relevant_documents(config)
    for i in range(5):
        print(f'Processing {arxivids[i]}')
        process(arxivids[i], data_manager, data)


if __name__ == '__main__':
    main()
