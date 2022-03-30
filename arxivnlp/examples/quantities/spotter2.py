import re
import sys
from typing import Any, Iterator, Optional, Tuple, Union

from lxml import etree

import arxivnlp.args
from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager
from arxivnlp.data.dnm import DnmRange, DnmPoint, DnmStr
from arxivnlp.examples.quantities import matchers
from arxivnlp.examples.quantities.center import PossibleFind, QuantityCenter, Scalars
from arxivnlp.examples.quantities.experiment import get_relevant_documents
from arxivnlp.examples.quantities.quantity_kb import QuantityKb, UnitNotation
from arxivnlp.examples.quantities.wikidata import QuantityWikiDataLoader


def try_read_number(dnm_str: DnmStr, offset: int) -> Optional[Tuple[Union[int, float], int]]:
    if not dnm_str.string[offset].isnumeric():
        return None
    numberstring = ''
    while offset < len(dnm_str) and dnm_str.string[offset] in {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.'}:
        numberstring += dnm_str.string[offset]
        offset += 1
    if numberstring.count('.') > 1:
        return None
    if '.' in numberstring:
        return float(numberstring), offset
    else:
        return int(numberstring), offset


def check_for_unit_at(dnm_str: DnmStr, offset: int) -> Optional[Tuple[PossibleFind, int]]:
    start_offset: int = offset
    scalar: Optional[Scalars] = None
    unit_notation: Optional[UnitNotation] = None

    # Look for text scalar
    r0 = try_read_number(dnm_str, offset)
    if r0:
        scalar = Scalars(float(r0[0]))
        offset = r0[1]

    # Skip potential space
    if dnm_str.string[offset].isspace():
        offset += 1

    # Process potential math node
    node = dnm_str.get_node(offset)
    if node.tag == 'math':
        if scalar is None:
            # Match for complete quantity (scalar + unit)
            matcher = (matchers.base / (matchers.quantity | matchers.quantity_in_rel)) ** 'root'
        else:
            matcher = (matchers.base / matchers.unit) ** 'root'

        matches = list(matcher.match(node))
        if matches:
            tree = matches[0].to_label_tree()
            if tree.has_child('scalar'):
                scalar = matchers.scalar_to_scalars(tree['scalar'])
            unit_notation = matchers.unit_to_unit_notation(tree['unit'])

    if unit_notation is not None:
        dnm_range = dnm_str.get_dnm_range(start_offset, offset)
        return PossibleFind(dnm_range=dnm_range, unit_notation=unit_notation, scalar=scalar), offset


def search(arxivid: str, data_manager: DataManager) -> Iterator[PossibleFind]:
    dnm = data_manager.load_dnm(arxivid)
    dnmstring: DnmStr = dnm.get_full_dnmstr()
    last_end: int = 0   # until where we have processed something
    for offset in (match.span()[0] for match in re.finditer('(MathNode)|[1-9]', dnmstring.string)):
        if offset >= last_end:
            result = check_for_unit_at(dnmstring, offset)
            if result is not None:
                last_end = result[1]
                yield result[0]

#     with data_manager.arxmliv_docs.open(arxivid) as fp:
#         dom = etree.parse(fp, html_parser)
#         for node in dom.xpath('//math'):
#             matches = list(matcher.match(node))
#             if not matches:
#                 continue
#             assert len(matches) == 1
#             tree = matches[0].to_label_tree()
#             scalars = matchers.scalar_to_scalars(tree['scalar'])
#             unit_notation = matchers.unit_to_unit_notation(tree['unit'])
#             dnm_range = DnmRange(DnmPoint(tree['unit'].children[0].node), DnmPoint(tree['unit'].children[0].node), right_closed=True)
#             yield PossibleFind(dnm_range=dnm_range, unit_notation=unit_notation, scalar=scalars)


def main():
    arxivnlp.args.auto()
    config = Config.get()
    data = QuantityWikiDataLoader(config).get()
    data_manager = DataManager(config)
    quantity_kb = QuantityKb.from_wikidata(data)
    quantity_center = QuantityCenter(data_manager, quantity_kb)
    arxivids = get_relevant_documents(config, data_manager)[:5]
    # arxivids = ['1710.04432']
    for arxivid in arxivids:
        print(f'Processing {arxivid}')
        possible_finds = list(search(arxivid, data_manager))
        quantity_center.process_finds(arxivid, possible_finds)


if __name__ == '__main__':
    main()
