from pathlib import Path
from typing import List, Any
import unicodedata

from lxml import etree

from arxivnlp import xml_match as xm
import arxivnlp.args
from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager
from arxivnlp.data.utils import require_other_data
from arxivnlp.examples.quantities.wikidata import QuantityWikiDataLoader, QuantityWikiData
from arxivnlp.xml_match import LabelTree


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
    relational_mo = xm.tag('mo').with_text('[' + ''.join({'=', '≈', '<', '>', '≪', '≫', '≥', '⩾', '≤', '⩽'}) + ']')
    simple_number = (xm.tag('mn') ** 'numeral' | xm.tag('mrow') / xm.seq(xm.tag('mo').with_text(r'[-–]') ** 'negative', xm.tag('mn') ** 'numeral')) ** 'simplenumber'
    power_of_10 = (xm.tag('msup')/xm.seq(xm.tag('mn').with_text('^10$'), simple_number ** 'exponent')) ** 'powerof10'
    scientific_number = (xm.tag('mrow') / xm.seq(simple_number ** 'factor', xm.tag('mtext').with_text('[×]'), power_of_10)) ** 'scientific'
    empty_tag = xm.any_tag.with_text('^$')
    scalar = ((simple_number | scientific_number | power_of_10 |
               (xm.tag('mrow') / xm.seq(empty_tag, xm.tag('mo').with_text(f'^{unicodedata.lookup("INVISIBLE TIMES")}$'), power_of_10))    # presumably this happens when using siunitx and leaving the factor empty
               ) ** 'scalar')
    space = xm.tag('mtext').with_text(r'\s*')
    simple_unit = (xm.tag('mi') | xm.tag('mrow')).with_class('ltx_unit') ** 'simpleunit'
    quantity = xm.tag('mrow') / xm.seq(scalar, xm.maybe(space), simple_unit)
    base = xm.tag('math') / xm.tag('semantics')
    quantity_in_rel = xm.tag('mrow') / xm.seq(xm.maybe(xm.any_tag), relational_mo, quantity)
    return base / (quantity | quantity_in_rel)


def mn_to_float(mn_text: str) -> float:
    reduced = ''
    for c in mn_text:
        if c.isnumeric():
            reduced += c
        elif c == '.':
            reduced += c
        elif c.isspace():
            continue
        else:
            print(f'Can\'t convert mn {repr(mn_text)}')
    return float(reduced)


def number_to_float(lt: LabelTree) -> float:
    if lt.label == 'simplenumber':
        sign = -1 if lt.has_child('negative') else 1
        return sign * mn_to_float(lt['numeral'].node.text)
    elif lt.label == 'scientific':
        return number_to_float(lt['factor']) * number_to_float(lt['powerof10'])
    elif lt.label == 'powerof10':
        return 10 ** number_to_float(lt['exponent'])
    elif len(lt.children) == 1:
        return number_to_float(lt.children[0])
    raise Exception(f'Unsupported tree: {lt}')


def process(arxivid: str, data_manager: DataManager, data: QuantityWikiData):
    html_parser: Any = etree.HTMLParser()  # Setting type to Any suppresses annoying warnings
    matcher = get_matcher()

    with data_manager.arxmliv_docs.open(arxivid) as fp:
        dom = etree.parse(fp, html_parser)
        for node in dom.xpath('//math'):
            matches = list(matcher.match(node))
            if not matches:
                if node.xpath('.//*[@class="ltx_unit"]'):
                    node.addnext(etree.XML('<span style="color:orange;font-size:150%"><b>o</b></span>'))
                continue
            assert len(matches) == 1
            tree = matches[0].to_label_tree()
            scalar = number_to_float(tree['scalar'])
            xrefs = tree['simpleunit'].node.xpath('./@xref')
            if not xrefs:
                continue
            xref = xrefs[0]
            # value = node.xpath(f'./ancestor::math//csymbol[@id="{xref}"]/text()')
            value = node.xpath(f'.//csymbol[@id="{xref}"]/text()')
            if not value:
                print('skipping')
                continue
            value = value[0]
            message = ''
            if value in data.label_to_unit:
                for unit in set(data.label_to_unit[value]):
                    message += f'<br/>{scalar} <a href="{unit.uri}">{value}</a>'
                    if unit.si_conversion is not None:
                        message += f' ≈ {scalar * unit.si_conversion} <a href="{unit.si_conversion_unit.uri}">{unit.si_conversion_unit.label}</a>'
            if not message:
                message = f'{scalar} {value}'
            node.addnext(etree.XML(f'<span><span class="arxivnlpmessagemarker">*</span><span class="arxivnlpmessage">{message}</span></span>'))
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
