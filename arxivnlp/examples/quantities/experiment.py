from pathlib import Path
from typing import List, Any, Optional, Union
import unicodedata

from lxml import etree

from arxivnlp import xml_match as xm
import arxivnlp.args
from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager
from arxivnlp.data.utils import require_other_data
from arxivnlp.examples.quantities.wikidata import QuantityWikiDataLoader, QuantityWikiData, Unit
from arxivnlp.xml_match import LabelTree


def get_relevant_documents(config: Config, dm: DataManager) -> List[str]:
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
    return sorted((a for a in d if dm.arxmliv_docs.arxiv_id_to_severity(a) != 'error'), key=lambda a: -d[a])


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
    mrow = xm.tag('mrow')

    relational_mo = xm.tag('mo').with_text('[' + ''.join({'=', '≈', '<', '>', '≪', '≫', '≥', '⩾', '≤', '⩽', '∼', '≲', '≳'}) + ']')
    empty_tag = xm.any_tag.with_text('^$')
    space = xm.tag('mtext').with_text(r'\s*')
    base = xm.tag('math') / xm.tag('semantics')

    # numbers and scalars
    simple_number = (xm.tag('mn') ** 'numeral' | mrow / xm.seq(xm.tag('mo').with_text(r'[-–]') ** 'negative',
                                                               xm.tag('mn') ** 'numeral')) ** 'simplenumber'
    power_of_10 = (xm.tag('msup') / xm.seq(xm.tag('mn').with_text('^10$'), simple_number ** 'exponent')) ** 'powerof10'
    scientific_number = (mrow / xm.seq(simple_number ** 'factor', xm.tag('mtext').with_text('[×]'),
                                       power_of_10)) ** 'scientific'
    scalar = ((simple_number | scientific_number | power_of_10 |
               (mrow / xm.seq(empty_tag, xm.tag('mo').with_text(f'^{unicodedata.lookup("INVISIBLE TIMES")}$'),
                              power_of_10))  # presumably this happens when using siunitx and leaving the factor empty
               ) ** 'scalar')

    # units
    simple_unit = xm.any_tag.with_class('ltx_unit') ** 'simpleunit'
    unit_power = (xm.tag('msup') / xm.seq(simple_unit ** 'unit', simple_number ** 'exponent')) ** 'unitpower'
    unit_times2 = (mrow / xm.seq(simple_unit | unit_power, xm.maybe(space), simple_unit | unit_power)) ** 'unittimes'
    unit_times3 = (mrow / xm.seq(simple_unit | unit_power, xm.maybe(space), simple_unit | unit_power, xm.maybe(space), simple_unit | unit_power)) ** 'unittimes'
    unit = (simple_unit | unit_power | unit_times2 | unit_times3) ** 'unit'

    # quantities
    quantity = mrow / xm.seq(scalar, xm.maybe(space), unit)
    quantity_in_rel = mrow / xm.seq(xm.maybe(xm.any_tag), relational_mo, quantity)
    return (base / (quantity | quantity_in_rel | unit)) ** 'root'


def mn_to_number(mn_text: str) -> Union[float, int]:
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
    return float(reduced) if '.' in reduced else int(reduced)


def tree_to_number(lt: LabelTree) -> Union[int, float]:
    if lt.label == 'simplenumber':
        sign = -1 if lt.has_child('negative') else 1
        return sign * mn_to_number(lt['numeral'].node.text)
    elif lt.label == 'scientific':
        return tree_to_number(lt['factor']) * tree_to_number(lt['powerof10'])
    elif lt.label == 'powerof10':
        return 10 ** tree_to_number(lt['exponent'])
    elif len(lt.children) == 1:
        return tree_to_number(lt.children[0])
    raise Exception(f'Unsupported tree: {lt}')


def unit_to_str(lt: LabelTree) -> Optional[str]:
    if lt.label == 'unit':
        assert len(lt.children) == 1
        return unit_to_str(lt.children[0])
    elif lt.label == 'simpleunit':
        xrefs = lt.node.xpath('./@xref')
        if not xrefs:
            print('missing xref')
            return None
        value = lt.node.xpath(f'./ancestor::math//csymbol[@id="{xrefs[0]}"]/text()')
        if not value:  # seems to happen if there are latexml errors
            return None
        return value[0]
    elif lt.label == 'unitpower':
        unit_str = unit_to_str(lt['unit'])
        if unit_str is None:
            return None
        exponent = tree_to_number(lt['exponent'])
        if exponent not in {-3, -2, -1, 1, 2, 3}:
            print(f'Unsupported exponent {exponent}')
            return None
        return {-3: 'per cubic ', -2: 'per square ', -1: 'per ', 1: '', 2: 'square ', 3: 'cubic '}[exponent] + unit_str
    elif lt.label == 'unittimes':
        parts = [unit_to_str(child) for child in lt.children]
        if any(part is None for part in parts):
            return None
        return ' '.join(parts)
    raise Exception(f'Unsupported tree: {lt}')


def find_unit(lt: LabelTree, data: QuantityWikiData) -> List[Unit]:
    string = unit_to_str(lt)
    if string is None:
        return []
    if string not in data.label_to_unit:
        # print(f'Unknown unit {string}')
        return []
    return data.label_to_unit[string]


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
            scalar = tree_to_number(tree['scalar']) if tree.has_child('scalar') else 1.0
            message = ''
            count = 0
            for unit in set(find_unit(tree['unit'], data)):
                count += 1
                message += f'<br/>{scalar} <a href="{unit.uri}">{unit.label}</a>'
                if unit.si_conversion is not None:
                    message += f' ≈ {scalar * unit.si_conversion} <a href="{unit.si_conversion_unit.uri}">{unit.si_conversion_unit.label}</a>'
            if not message:
                message = f'{scalar} {unit_to_str(tree["unit"])}'
            star = '*'
            if count != 1:
                star = f'<span style="color:purple">{star}</span>'
            node.addnext(etree.XML(
                f'<span><span class="arxivnlpmessagemarker">{star}</span><span class="arxivnlpmessage">{message}</span></span>'))
        dom.xpath('.//head')[0].append(etree.XML(f'<style>{CSS}</style>'))  # TODO: Escape CSS
        with open(f'/tmp/units-{arxivid}.html', 'wb') as fp:
            fp.write(etree.tostring(dom))


def main():
    arxivnlp.args.auto()
    config = Config.get()
    data = QuantityWikiDataLoader(config).get()
    data_manager = DataManager(config)
    arxivids = get_relevant_documents(config, data_manager)
    for i in range(5):
        print(f'Processing {arxivids[i]}')
        process(arxivids[i], data_manager, data)


if __name__ == '__main__':
    main()
