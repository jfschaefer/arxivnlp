"""
The "control center" for quantity collection (still looking for a better name).
"""
import enum
import gzip
import io
import json
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Iterator

from arxivnlp.data.datamanager import DataManager
from arxivnlp.data.dnm import DnmRange
from arxivnlp.examples.quantities.quantity_kb import Certainty, UnitNotation, QuantityKb


class ScalarNotation(enum.IntFlag):
    SCIENTIFIC = enum.auto()  # scientific notation (x * 10^n)
    PLUS_MINUS = enum.auto()  # x ± ε
    DASH_RANGE = enum.auto()  # x - y
    TEXT_RANGE = enum.auto()  # x to y, between x and y
    IN_TEXT = enum.auto()  # at least one of the numbers is not in math mode


@dataclass
class Scalars(object):
    # the main value (for simple ranges the start)
    value: float
    # the upper bound of a range
    range_upper: Optional[float] = None
    # the lower bound of ranges with a "main value" (e.g. in 5 ± 2)
    range_lower: Optional[float] = None
    scalar_notation: ScalarNotation = ScalarNotation(0)


class UnitNotationProperties(enum.IntFlag):
    IN_TEXT = enum.auto()  # at least part of the notation is not in math mode
    ONLY_TEXT = enum.auto()  # all of the notation is not in text mode
    SPACE_SEP = enum.auto()  # separated by some space from the scalar


@dataclass
class PossibleFind(object):
    dnm_range: DnmRange
    unit_notation: UnitNotation
    unit_notation_properties: UnitNotationProperties = UnitNotationProperties(0)
    scalar: Optional[Scalars] = None


@dataclass
class Occurrence(object):
    arxivid: str
    certainty: Certainty
    dnm_range: str

    unit_id: int
    unit_notation: str
    unit_notation_properties: UnitNotationProperties

    amount_notation: Optional[ScalarNotation] = None
    amount_val: Optional[float] = None

    # in case of range: re_* refers to end of range
    re_amount_val: Optional[float] = None
    re_unit_id: Optional[int] = None
    re_unit_notation: Optional[str] = None

    # in case the range is actually one value with error bars
    # (e.g. in x ± y, we would have amount_val = x-y, re_amount_val = x+y, amount_center_val = y)
    amount_center_val: Optional[float] = None

    quantity: List[int] = field(default_factory=list)
    # pairs of actual string and dnm range, note that json recovery results in List[List[str]]
    quantity_strings: List[Tuple[str]] = field(default_factory=list)
    quantity_notation: Optional[str] = None

    logs: str = ''

    def to_json(self) -> str:
        d = {}
        # only use relevant elements to reduce size
        for key, val in self.__dict__.items():
            if val is None:
                continue
            if type(val) == list and len(val) == 0:
                continue
            d[key] = val
        return json.dumps(d)

    @classmethod
    def from_json(cls, jsonstr: str) -> 'Occurrence':
        return Occurrence(**json.loads(jsonstr))


class QuantityCenter(object):
    def __init__(self, data_manager: DataManager, quantity_kb: QuantityKb):
        self.data_manager = data_manager
        self.config = self.data_manager.config
        self.quantity_kb = quantity_kb
        self.directory = self.config.other_data_dir / 'quantity-spotter'

    def process_finds(self, arxivid: str, possible_finds: List[PossibleFind]):
        self.directory.mkdir(exist_ok=True)
        with io.TextIOWrapper(gzip.open(self.directory / f'{arxivid}.gz', 'w')) as fp:
            for possible_find in possible_finds:
                if possible_find.unit_notation in self.quantity_kb.unit_notation_to_units:
                    unit = self.quantity_kb.unit_notation_to_units[possible_find.unit_notation][0]
                    occurrence = Occurrence(
                        arxivid=arxivid, certainty=Certainty.RATHER_YES, dnm_range=possible_find.dnm_range.to_string(),
                        unit_id=unit.id,
                        unit_notation=possible_find.unit_notation.to_json(),
                        unit_notation_properties=UnitNotationProperties(0)
                    )
                    fp.write(occurrence.to_json() + '\n')

    def load_occurrences(self, arxivid: str) -> Iterator[Occurrence]:
        with gzip.open(self.directory / f'{arxivid}.gz', 'r') as fp:
            for line in fp:
                line = line.strip()
                if line:
                    yield Occurrence.from_json(line)
