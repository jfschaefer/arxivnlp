import enum
from dataclasses import dataclass, field
from enum import IntEnum, Flag
from typing import Dict, List, Optional, Tuple

from arxivnlp.examples.quantities.dimension import Dimension
from arxivnlp.examples.quantities.wikidata import QuantityWikiData
from arxivnlp.utils import from_superscript


@dataclass
class Notation(object):
    nodetype: str
    attr: Dict[str, str]
    children: List['Notation']

    def __post_init__(self):
        n_children = {'i': 0, 'sup': 2, 'sub': 2, 'supsub': 3}
        assert self.nodetype in n_children
        assert len(self.children) == n_children[self.nodetype]

    def __lt__(self, other) -> bool:
        """ an arbitrary strict total order -- TODO: Is there an easier way? """
        if self.nodetype < other.nodetype:
            return True
        if self.nodetype > other.nodetype:
            return False
        if len(self.children) < len(other.children):
            return True
        if len(self.children) > len(other.children):
            return False
        for sc, oc in zip(self.children, other.children):
            if sc < oc:
                return True
            if sc > oc:
                return False
        if len(self.attr) < len(other.attr):
            return True
        if len(self.attr) > len(other.attr):
            return False
        for c in sorted(self.attr.keys()):
            if self.attr[c] < other.attr[c]:
                return True
            elif self.attr[c] > other.attr[c]:
                return False
        return False  # they're equal

    def __eq__(self, other):
        return self.nodetype == other.nodetype and len(self.children) == len(other.children) and \
            all(sc == oc for sc, oc in zip(self.children, other.children)) and \
            len(self.attr) == len(other.attr) and all(self.attr[k] == other.attr[k] for k in self.attr)

    def __gt__(self, other):
        return (not self < other) and not self == other



@dataclass
class UnitNotation(object):
    parts: List[Tuple[Notation, int]]

    def __post_init__(self):
        self.parts.sort()

    @classmethod
    def from_wikidata_string(cls, full_string: str) -> 'UnitNotation':
        string: str = full_string.strip()
        cur_id: str = ''
        in_denominator: bool = False
        exponent: str = ''
        parts: List[Tuple[Notation, int]] = []

        def push():
            nonlocal cur_id, parts, exponent
            if not cur_id:
                print('WARNING', repr(full_string), parts)
            e = int(exponent) if exponent else 1
            if in_denominator:
                e = -e
            parts.append((Notation('i', {'val': cur_id}, []), e))
            cur_id = ''
            exponent = ''

        for i, c in enumerate(string):
            if c in from_superscript:
                exponent += from_superscript[c]
            elif c.isspace():
                if string[i + 1] != '(':
                    push()
            elif c == '(':
                if in_denominator:
                    continue
                cur_id += c
            elif c == ')':
                if '(' in cur_id:
                    cur_id += c
                continue
            elif c == '/':
                push()
                in_denominator = True
            else:
                cur_id += c
        push()
        unit_notation = UnitNotation(parts)
        # print(full_string, unit_notation)
        return unit_notation

    def __hash__(self):
        return id(self)


class Certainty(IntEnum):
    CERTAINLY_NOT = 0  # human said so
    PROBABLY_NOT = 1
    UNCLEAR = 2
    RATHER_YES = 3
    PROBABLY_YES = 4
    CERTAINLY_YES = 5  # human said so


class Creation(Flag):
    MANUAL = enum.auto()
    WIKIDATA = enum.auto()
    COMBINED = enum.auto()  # new combination of known data
    GUESS = enum.auto()
    CONFIRMED = enum.auto()  # human looked at it
    UNKOWN = enum.auto()


class MetaData(object):
    __slots__ = ['counts', 'creation', 'logs']

    def __init__(self, creation: Creation = Creation.UNKOWN):
        self.counts: Dict[Certainty, int] = {c: 0 for c in Certainty}
        self.creation: Creation = creation
        self.logs: str = ''


@dataclass
class Unit(object):
    id: int = -1
    display_name: Optional[str] = None
    string_names: Dict[str, MetaData] = field(default_factory=dict)
    notations: Dict[UnitNotation, MetaData] = field(default_factory=dict)
    symbols: Dict[Notation, MetaData] = field(default_factory=dict)  # e.g. λ for nm (as in "λ = 740 nm")
    quantities: Dict['Quantity', MetaData] = field(default_factory=dict)
    conversion_factor: Optional[float] = None
    conversion_unit: Optional['Unit'] = None
    dimension: Optional[Dimension] = None
    dimension_certainty: Optional[Certainty] = None
    creation: Creation = Creation.UNKOWN


@dataclass
class Quantity(object):
    id: int = -1
    display_name: Optional[str] = None
    string_names: Dict[str, MetaData] = field(default_factory=dict)
    notations: Dict[Notation, MetaData] = field(default_factory=dict)  # analog to Unit.symbols
    parents: Dict['Quantity', Creation] = field(default_factory=dict)
    # multiple dimensions used in practice (e.g. force of 5 kg)
    dimensions: Dict[Dimension, MetaData] = field(default_factory=dict)
    creation: Creation = Creation.UNKOWN

    def __hash__(self):
        return id(self)


class QuantityKb(object):
    def __init__(self):
        self.all_units: List[Unit] = []
        self.all_quantities: List[Quantity] = []

    def add_unit(self, unit: Unit):
        assert unit.id == -1
        unit.id = len(self.all_units)
        self.all_units.append(unit)

    def add_quantity(self, quanitity: Quantity):
        assert quanitity.id == -1
        quanitity.id = len(self.all_quantities)
        self.all_quantities.append(quanitity)

    @classmethod
    def from_wikidata(cls, qwd: QuantityWikiData) -> 'QuantityKb':
        kb = QuantityKb()

        # quantities
        q_wd_to_kb = {}
        for quantity in qwd.quantities:
            q = Quantity(
                display_name=quantity.label,
                string_names={l: MetaData(Creation.WIKIDATA) for l in quantity.alt_labels + [quantity.label]},
                creation=Creation.WIKIDATA,
                dimensions={quantity.dimension: MetaData(Creation.WIKIDATA)} if quantity.dimension is not None else {},
            )
            q_wd_to_kb[quantity] = q
            kb.add_quantity(q)
        for quantity in qwd.quantities:
            q_wd_to_kb[quantity].parents = {q_wd_to_kb[p]: Creation.WIKIDATA for p in quantity.parents}

        # units
        u_wd_to_kb = {}
        for unit in qwd.units:
            u = Unit(
                display_name=unit.label,
                string_names={l: MetaData(Creation.WIKIDATA) for l in unit.alt_labels + [unit.label]},
                quantities={q_wd_to_kb[quantity]: MetaData(Creation.WIKIDATA) for quantity in unit.quantities},
                dimension=unit.dimension,
                dimension_certainty=Certainty.CERTAINLY_YES,
                # TODO: Notations should be in central lookup-tree, etc.
                notations={UnitNotation.from_wikidata_string(s): MetaData(Creation.WIKIDATA | Creation.GUESS) for s in
                           unit.notations}
            )
            u_wd_to_kb[unit] = u
            kb.add_unit(u)
        for unit in qwd.units:
            if unit not in u_wd_to_kb:
                print('unit not in dict:', unit.label, unit.identifier)
                continue
            u: Unit = u_wd_to_kb[unit]
            if unit.si_conversion_unit is not None and unit.si_conversion_unit is not None:
                u.conversion_factor = unit.si_conversion
                u.conversion_unit = u_wd_to_kb[unit.si_conversion_unit]
        return kb


@dataclass
class Occurrence(object):
    arxivid: str
    certainty: Certainty

    unit_id: int
    unit_ref: str
    unit_notation: str

    amount_ref: Optional[str] = None
    amount_val: Optional[float] = None

    # in case of range: re_* refers to end of range
    re_amount_ref: Optional[str] = None
    re_amount_val: Optional[float] = None
    re_unit_id: Optional[int] = None
    re_unit_ref: Optional[str] = None
    re_unit_notation: Optional[str] = None

    # in case the range is actually one value with error bars
    # (e.g. in x ± y, we would have amount_val = x-y, re_amount_val = x+y, amount_center_val = y)
    amount_center_val: Optional[float] = None

    quantity: List[int] = field(default_factory=list)
    quantity_notation: List[str] = field(default_factory=list)

    logs: str = ''
