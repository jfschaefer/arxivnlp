import csv
import gzip
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Dict, Set, Any

import requests
from lxml import etree

from arxivnlp.config import Config
from arxivnlp.data.cached import CachedData
from arxivnlp.data.exceptions import MissingDataException
from arxivnlp.data.utils import require_other_data
from arxivnlp.utils import superscript_int


def wikidata_sparql_query(query: str) -> str:
    logger = logging.getLogger(__name__)
    logger.info('Sending SPARQL query to query.wikidata.org')
    result = requests.get('https://query.wikidata.org/sparql', params={'query': query}, headers={'Accept': 'text/csv'})
    if not result.ok:
        logger.error(f'Got response {result.status_code} from query.wikidata.org')
        raise MissingDataException('Failed to get data from wikidata:\n' + result.text)
    return result.text


class Dimension(object):
    # time, length, mass, electirc current, abs. temperature, amount of subst., luminous intensity
    dim_order: List[str] = list('TLMIΘNJ')
    acceptable_dims: Set[str] = set(dim_order)

    def __init__(self, dims: Dict[str, int]):
        assert all(dim in self.acceptable_dims for dim in dims)
        self.dims = dims

    def __str__(self) -> str:
        """ Unique string representation """
        s: str = ''
        for d in self.dim_order:
            if d in self.dims and self.dims[d]:
                s += f'{d}{superscript_int(self.dims[d])}'
        if not s:
            s = '1'
        return s

    def __eq__(self, other) -> bool:
        return str(self) == str(other)

    def __neq__(self, other) -> bool:
        return str(self) != str(other)

    @classmethod
    def from_wikidata_mathml(cls, mathml: str) -> 'Dimension':
        """ this code is brittle and may break if the WikiData MathML representation for dimensions changes """
        tree = etree.XML(mathml)
        no_dim = False
        dims: Dict[str, int] = {}
        node: Any
        for node in tree.xpath('//*[local-name()="mstyle"]/*'): # type: ignore
            assert not no_dim
            if node.tag == '{http://www.w3.org/1998/Math/MathML}mn':
                assert node.text.strip() == '1'
                no_dim = True
            elif node.tag == '{http://www.w3.org/1998/Math/MathML}mi':
                char = node.text.strip()
                assert char not in dims
                dims[char] = 1
            elif node.tag == '{http://www.w3.org/1998/Math/MathML}mrow':
                char = node.xpath('.//*[local-name()="mi"]/text()')[0].strip()
                assert char not in dims
                dims[char] = 1
            elif node.tag == '{http://www.w3.org/1998/Math/MathML}msup':
                char = node.xpath('.//*[local-name()="mi"]/text()')[0].strip()
                assert char not in dims
                n = int(node.xpath('.//*[local-name()="mn"]/text()')[0].strip())
                if node.xpath('.//*[local-name()="mo"]'):
                    n *= -1
                dims[char] = n
            else:
                print(mathml)
                raise Exception(f'Unexpected tag: {node.tag}')
        return Dimension(dims)


# def notation_norm(notation: str) -> Set[str]:
#     """ given a string notation, it generates different, standardized variants """
#     variants: Set[str] = set()
#     # replace superscript and subscript
#     replacements = {
#         # superscript numbers
#         '⁻': '^-', '⁰': '^0', '¹': '^1', '²': '^2', '³': '^3', '⁴': '^4', '⁵': '^5', '⁶': '^6', '⁷': '^7', '⁸': '^8', '⁹': '^9',
#         # subscript numbers
#         '₋': '_-', '₀': '_0', '₁': '_1', '₂': '_2', '₃': '_3', '₄': '_4', '₅': '_5', '₆': '_6', '₇': '_7', '₈': '_8', '₉': '_9'
#                     }
#     new_notation = ''.join(replacements[c] if c in replacements else c for c in notation)
#     # TODO: s^-1 vs s^-^1 vs s^(-1)
#     variants.add(new_notation)
#
#     for variant in list(variants):
#         variants.add(variant.replace('º', '^∘'))
#     for variant in list(variants):
#         if '_☉' not in variant:
#             variants.add(variant.replace('☉', '_☉'))
#     for variant in list(variants):
#         variants.add(variant.replace('☉', '⊙'))
#
#     # TODO: More variants e.g. "m/s" vs "m s^-^1" vs "s^-1 m" (this gets tricky for more complex ones)
#     return variants


class Quantity(object):
    def __init__(self, identifier: str, label: str):
        self.identifier = identifier
        self.label = label
        self.alt_labels: List[str] = []
        self.parents: List['Quantity'] = []
        self.dimension: Optional[Dimension] = None
        self.symbols: Set[str] = set()

    @property
    def uri(self) -> str:
        return f'https://www.wikidata.org/entity/{self.identifier}'


class Unit(object):
    def __init__(self, identifier: str, label: str):
        self.identifier = identifier
        self.label = label
        self.alt_labels: List[str] = []
        self.quantities: List[Quantity] = []
        self.dimension: Optional[Dimension] = None
        self.notations: Set[str] = set()
        self.si_conversion: Optional[float] = None
        self.si_conversion_unit: Optional['Unit'] = None

    @property
    def uri(self) -> str:
        return f'https://www.wikidata.org/entity/{self.identifier}'


class QuantityWikiData(object):
    def __init__(self, quantities: List[Quantity], units: List[Unit]):
        self.quantities = quantities
        self.units = units

        self.label_to_unit: Dict[str, List[Unit]] = {}
        for unit in self.units:
            self.label_to_unit.setdefault(unit.label, []).append(unit)
            for alt_label in unit.alt_labels:
                if len(alt_label) > 4:
                    self.label_to_unit.setdefault(alt_label, []).append(unit)


class QuantityWikiDataLoader(object):
    def __init__(self, config: Config):
        self.config = config
        self.data: CachedData[QuantityWikiData] = CachedData(self.config, 'quantities-wikidata')

    def get(self) -> QuantityWikiData:
        if self.data.ensured():
            assert self.data.data is not None
            return self.data.data

        # STEP 1: COMPILE QUANTITY DATA
        quantities: Dict[str, Quantity] = {}
        dim_collection: Dict[str, Dimension] = {}
        quant_parents: Dict[str, List[str]] = {}
        with self.load_csv('quantities', ['quantity', 'quantityLabel', 'dimension', 'super_quantities', 'symbols',
                                          'symbols_ltx', 'altLabels']) as quantities_reader:
            for quantity, quantityLabel, dimension, super_quantities, symbols, symbols_ltx, alt_labels \
                    in quantities_reader:
                identifier = quantity.split('/')[-1]
                new_quant = Quantity(identifier, quantityLabel)
                assert identifier not in quantities
                quantities[identifier] = new_quant
                if dimension.strip():
                    real_dim = Dimension.from_wikidata_mathml(dimension)
                    # idea: only one object per dimension to make pickle dump smaller
                    if str(real_dim) in dim_collection:
                        real_dim = dim_collection[str(real_dim)]
                    else:
                        dim_collection[str(real_dim)] = real_dim
                    new_quant.dimension = real_dim
                if super_quantities.strip():
                    quant_parents[identifier] = [s.strip().split('/')[-1] for s in super_quantities.split('❙')]

        # STEP 2: LINK QUANTITY DATA
        for quant_id in quant_parents:
            quantity = quantities[quant_id]
            for q2 in quant_parents[quant_id]:
                if q2 in quantities:
                    quantity.parents.append(quantities[q2])
        # copy dimensions (implementation could be optimized, but it's fast enough)
        # Note that diamonds and maybe even cycles are possible
        something_changed: bool = True
        while something_changed:
            something_changed = False
            for q in quantities.values():
                for p in q.parents:
                    if p.dimension is not None and q.dimension is None:
                        q.dimension = p.dimension
                        something_changed = True

        # STEP 3: COMPILE UNIT DATA
        units: Dict[str, Unit] = {}
        si_conv_unit: Dict[Unit, str] = {}
        with self.load_csv('units', ['unit', 'unitLabel', 'quantities', 'SIamounts', 'SIunit',
                                     'notations', 'altLabels']) as units_reader:
            for unit_uri, unitLabel, unit_quantities, si_amounts, si_unit, notations, alt_labels in units_reader:
                identifier = unit_uri.split('/')[-1]
                assert identifier not in units
                units[identifier] = Unit(identifier, unitLabel)
                unit = units[identifier]
                unit.alt_labels = alt_labels.strip().split('❙')
                if unit_quantities.strip():
                    for qstr in unit_quantities.split('❙'):
                        qq = qstr.strip().split('/')[-1]
                        if qq in quantities:
                            quant = quantities[qq]
                            assert quant not in unit.quantities
                            unit.quantities.append(quant)
                            if quant.dimension is not None:
                                # if unit.dimension is not None and quant.dimension != unit.dimension:
                                #     print(unit.identifier, unit.label, unit.dimension, quant.identifier, quant.label, quant.dimension)
                                unit.dimension = quant.dimension
                if si_amounts.strip():
                    # for now, pick only the first one
                    unit.si_conversion = float(si_amounts.split('❙')[0])
                    si_conv_unit[unit] = si_unit.split('/')[-1]
        for unit, si_unit_id in si_conv_unit.items():
            unit.si_conversion_unit = units[si_unit_id]

        self.data.data = QuantityWikiData(list(quantities.values()), list(units.values()))
        # TODO: write data to cache (once pre-processing has converged)

        return self.data.data

    @contextmanager
    def load_csv(self, queryname: str, assert_columns: Optional[List[str]] = None):
        try:
            path = require_other_data(self.config, Path('quantities') / f'wikidata-{queryname}.csv.gz')
        except MissingDataException:
            path = self.download(queryname)
        fp = gzip.open(path, mode='rt')
        try:
            reader = csv.reader(fp, delimiter=',', quotechar='"', doublequote=True)
            header = next(reader)
            if assert_columns is not None:
                for x, y in zip(header, assert_columns):
                    if x != y:
                        raise Exception(f'Expected column {x} but found {y} in wikidata-{queryname}.csv')
            yield reader
        finally:
            fp.close()

    def download(self, queryname: str) -> Path:
        if self.config.other_data_dir is None:
            raise Exception('No directory for other data was specified in the config')
        path = self.config.other_data_dir / 'quantities'
        path.mkdir(exist_ok=True)
        logger = logging.getLogger(__name__)
        logger.info(f'Downloading quantity data "{queryname}" from wikidata')
        queryfile = Path(__file__).parent / 'sparql' / f'{queryname}.query'
        with open(queryfile) as queryfp:
            outfile = path / ('wikidata-' + queryname + '.csv.gz')
            with gzip.open(outfile, compresslevel=3, mode='wt') as outfp:
                outfp.write(wikidata_sparql_query(queryfp.read()))
            logger.info(f'Created {outfile}')
            return outfile


if __name__ == '__main__':
    import arxivnlp.args

    arxivnlp.args.auto()
    data = QuantityWikiDataLoader(Config.get()).get()
