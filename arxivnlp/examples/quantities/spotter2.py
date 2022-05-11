import re
from typing import Iterator, Optional, Tuple, Union, List

from lxml.etree import _Element

from arxivnlp import xml_match as xm
import arxivnlp.args
from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager
from arxivnlp.data.dnm import DnmStr
from arxivnlp.examples.quantities import matchers
from arxivnlp.examples.quantities.center import PossibleFind, QuantityCenter, Scalars, ScalarNotation
from arxivnlp.examples.quantities.experiment import get_relevant_documents
from arxivnlp.examples.quantities.quantity_kb import QuantityKb, UnitNotation, Notation
from arxivnlp.examples.quantities.wikidata import QuantityWikiDataLoader
from arxivnlp.utils import cprint, Color


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


class Checker(object):
    def __init__(self, dnm_str: DnmStr, offset: int):
        self.dnm_str = dnm_str
        self.start_offset = offset
        self.offset = offset

        self.done: bool = False
        self.scalar: Optional[Scalars] = None
        self.space_after_scalar: Optional[bool] = None
        self.unit_notation: Optional[UnitNotation] = None
        self.relational_symbol: Optional[Notation] = None
        self.quant_symbol: Optional[Notation] = None

    def run(self) -> Optional[Tuple[PossibleFind, int]]:
        while not self.done:
            node = self.dnm_str.get_node(self.offset)
            if node.tag == 'math':
                self.process_math(node)
                while self.dnm_str.get_node(self.offset) == node:
                    self.offset += 1
            else:
                self.process_text()
        if self.unit_notation is not None:
            dnm_range = self.dnm_str.get_dnm_range(self.start_offset, self.offset)
            return PossibleFind(dnm_range=dnm_range, unit_notation=self.unit_notation, scalar=self.scalar), self.offset

    def process_math(self, node: _Element):
        sub_matchers: List[xm.NodeMatcher] = []
        if self.scalar is None:
            sub_matchers.append(matchers.quantity)
            if self.relational_symbol is None:
                sub_matchers.append(matchers.quantity_in_rel)
        else:
            sub_matchers.append(matchers.unit)

        matcher = (matchers.base / xm.MatcherNodeOr(sub_matchers)) ** 'root'
        matches = list(matcher.match(node))
        if not matches:
            self.done = True
            return
        if len(matches) > 1:
            print(f'DEBUG: Multiple matches:', matches)
        tree = matches[0].to_label_tree()
        if 'scalar' in tree:
            if self.scalar is not None:
                print(f'DEBUG: Found second scalar')
                self.done = True
                return
            self.scalar = matchers.scalar_to_scalars(tree['scalar'])

        if 'unit' in tree:
            if self.unit_notation is not None:
                print('DEBUG: Unit got extended?')
                self.done = True
                return
            self.unit_notation = matchers.unit_to_unit_notation(tree['unit'])

    def process_text(self):
        if self.scalar is None:
            result = try_read_number(self.dnm_str, self.offset)
            if result is not None:
                scalar_notation = ScalarNotation.IN_TEXT
                if type(result[0]) == int:
                    scalar_notation = scalar_notation | ScalarNotation.IS_INT
                self.scalar = Scalars(float(result[0]), scalar_notation=scalar_notation)
                self.offset = result[1]
                return
            self.done = True  # no scalar found
            return

        if self.unit_notation is None:
            if self.dnm_str.string[self.offset].isspace():
                self.offset += 1
                self.space_after_scalar = True
                return

        self.done = True


def search(arxivid: str, data_manager: DataManager) -> Iterator[PossibleFind]:
    dnm = data_manager.load_dnm(arxivid)
    dnmstring: DnmStr = dnm.get_full_dnmstr()
    last_end: int = 0  # until where we have processed something
    for offset in (match.span()[0] for match in re.finditer('(MathNode)|[1-9]', dnmstring.string)):
        if offset >= last_end:
            checker = Checker(dnmstring, offset)
            result = checker.run()
            if result is not None:
                last_end = result[1]
                yield result[0]


def main():
    arxivnlp.args.auto()
    config = Config.get()
    data = QuantityWikiDataLoader(config).get()
    data_manager = DataManager(config)
    quantity_kb = QuantityKb.from_wikidata(data)
    quantity_center = QuantityCenter(data_manager, quantity_kb)
    arxivids = get_relevant_documents(config, data_manager)[:5]
    arxivids = ['1707.03517']
    for arxivid in arxivids:
        cprint([Color.BOLD], f'Processing {arxivid}')
        possible_finds = list(search(arxivid, data_manager))
        cprint([Color.BOLD], f'    -> {len(possible_finds)} matches')
        quantity_center.process_finds(arxivid, possible_finds)


if __name__ == '__main__':
    main()
