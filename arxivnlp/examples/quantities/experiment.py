from pathlib import Path
from typing import List, Any

from lxml import etree

from arxivnlp import xml_match as xm
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

CSS = '''
.arxivnlpmessage {
  display: none;
  position: absolute;
  background-color: #ddddaa;
  border-style: solid;
  border-color: #330000;
  padding: 10px;
  font-size: 24pt;
}

.arxivnlpmessagemarker:hover + .arxivnlpmessage {
  display: block;
}

.arxivnlpmessagemarker {
  font-weight: bold;
  font-size: 150%;
  color: red;
}
'''


def get_matcher() -> xm.NodeMatcher:
    scalar = xm.tag('mn') ** 'scalar'
    space = xm.tag('mtext').with_text(r'\s*')
    unit = (xm.tag('mi') | xm.tag('mrow')).with_class('ltx_unit') ** 'unit'
    quantity = xm.tag('mrow') / xm.seq(scalar, xm.maybe(space), unit)
    base = xm.tag('math') / xm.tag('semantics')
    return base / quantity


def process(arxivid: str, data_manager: DataManager, data: QuantityWikiData):
    html_parser: Any = etree.HTMLParser()  # Setting type to Any suppresses annoying warnings

    matcher = get_matcher()

    with data_manager.arxmliv_docs.open(arxivid) as fp:
        dom = etree.parse(fp, html_parser)
        for node in dom.xpath('//math'):
            matches = list(matcher.match(node))
            if not matches:
                continue
            assert len(matches) == 1
            tree = matches[0].to_label_tree()
            scalar = tree['scalar'].node.text
            xrefs = tree['unit'].node.xpath('./@xref')
            if not xrefs:
                continue
            xref = xrefs[0]
            # value = node.xpath(f'./ancestor::math//csymbol[@id="{xref}"]/text()')
            value = node.xpath(f'.//csymbol[@id="{xref}"]/text()')
            if not value:
                print('skipping')
                continue
            value = value[0]
            node.addnext(etree.XML(f'<span><span class="arxivnlpmessagemarker">*</span><span class="arxivnlpmessage">{scalar} {value}</span></span>'))
        dom.xpath('.//head')[0].append(etree.XML(f'<style>{CSS}</style>'))  # TODO: Escape CSS
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
