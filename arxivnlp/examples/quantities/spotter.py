import unicodedata
from typing import Union, Any, Iterator

from lxml import etree

import arxivnlp.args
from arxivnlp import xml_match as xm
from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager
from arxivnlp.data.dnm import DnmRange, DnmPoint
from arxivnlp.examples.quantities.center import PossibleFind, QuantityCenter
from arxivnlp.examples.quantities.experiment import get_relevant_documents
from arxivnlp.examples.quantities.quantity_kb import QuantityKb, UnitNotation, Notation
from arxivnlp.examples.quantities.wikidata import QuantityWikiDataLoader
from arxivnlp.xml_match import LabelTree


def get_matcher() -> xm.NodeMatcher:
    mrow = xm.tag('mrow')

    relational_mo = xm.tag('mo').with_text(
        '[' + ''.join({'=', '≈', '<', '>', '≪', '≫', '≥', '⩾', '≤', '⩽', '∼', '≲', '≳'}) + ']')
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
    simple_unit = (xm.tag('mi') |
                   xm.tag('mo')       # e.g. for "%"
                   ) ** 'simpleunit'   # TODO: expand this
    unit_power = (xm.tag('msup') / xm.seq(simple_unit, simple_number ** 'exponent')) ** 'unitpower'
    unit_times2 = (mrow / xm.seq(simple_unit | unit_power, xm.maybe(space), simple_unit | unit_power)) ** 'unittimes'
    unit_times3 = (mrow / xm.seq(simple_unit | unit_power, xm.maybe(space), simple_unit | unit_power, xm.maybe(space),
                                 simple_unit | unit_power)) ** 'unittimes'
    unit = (simple_unit | unit_power | unit_times2 | unit_times3) ** 'unit'

    # quantities
    quantity = mrow / xm.seq(scalar, xm.maybe(space), unit)
    quantity_in_rel = mrow / xm.seq(xm.maybe(xm.any_tag), relational_mo, quantity)
    return (base / (quantity | quantity_in_rel)) ** 'root'


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


def simple_unit_to_notation(lt: LabelTree) -> Notation:
    node = lt.node
    attr = {'val': node.text}
    if node.tag == 'mi' and node.text and len(node.text) == 1 and node.get('mathvariant') != 'normal':
        attr['isitalic'] = True
    #     mv = node.get('mathvariant')
    #     if mv:
    #         attr['mathvariant'] = mv
    #     if node.tag == 'mo' and not mv:
    #         attr['mathvariant'] = 'normal'
    return Notation('i', attr, [])


class UnconvertableException(Exception):
    pass


def unit_to_unit_notation(lt: LabelTree) -> UnitNotation:
    if lt.label == 'unit':
        assert len(lt.children) == 1
        return unit_to_unit_notation(lt.children[0])
    elif lt.label == 'simpleunit':
        notation = simple_unit_to_notation(lt)
        return UnitNotation([(notation, 1)])
    elif lt.label == 'unitpower':
        notation = simple_unit_to_notation(lt['simpleunit'])
        exponent = tree_to_number(lt['exponent'])
        if exponent not in range(-10, 10):
            raise UnconvertableException(f'Bad exponent: {exponent}')
        return UnitNotation([(notation, exponent)])
    elif lt.label == 'unittimes':
        parts = []
        for subunit in lt.children:
            parts += unit_to_unit_notation(subunit).parts
        return UnitNotation(parts)
    raise Exception(f'Unsupported node: {lt.label}')


def search(arxivid: str, data_manager: DataManager) -> Iterator[PossibleFind]:
    html_parser: Any = etree.HTMLParser()  # Setting type to Any suppresses annoying warnings
    matcher = get_matcher()

    with data_manager.arxmliv_docs.open(arxivid) as fp:
        dom = etree.parse(fp, html_parser)
        for node in dom.xpath('//math'):
            matches = list(matcher.match(node))
            if not matches:
                if node.xpath('.//*[@class="ltx_unit"]'):
                    print('no match despit ltx_unit')
                continue
            print('matches')
            assert len(matches) == 1
            tree = matches[0].to_label_tree()
            scalar = tree_to_number(tree['scalar'])
            unit_notation = unit_to_unit_notation(tree['unit'])
            print(tree['unit'].node, tree['unit'].children, tree['unit'].children[0].node)
            dnm_range = DnmRange(DnmPoint(tree['unit'].children[0].node), DnmPoint(tree['unit'].children[0].node), right_closed=True)
            yield PossibleFind(dnm_range=dnm_range, unit_notation=unit_notation)


def main():
    arxivnlp.args.auto()
    config = Config.get()
    data = QuantityWikiDataLoader(config).get()
    data_manager = DataManager(config)
    quantity_kb = QuantityKb.from_wikidata(data)
    quantity_center = QuantityCenter(data_manager, quantity_kb)
    arxivids = get_relevant_documents(config, data_manager)[:5]
    # arxivids = ['astro-ph0604002']
    for arxivid in arxivids:
        print(f'Processing {arxivid}')
        possible_finds = list(search(arxivid, data_manager))
        quantity_center.process_finds(arxivid, possible_finds)


if __name__ == '__main__':
    main()
