import csv
import gzip
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Dict, Set
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
        s: str = ''
        for d in self.dim_order:
            if d in self.dims:
                s += f'{d}{superscript_int(self.dims[d])}'
        if not s:
            s = '1'
        return s

    @classmethod
    def from_wikidata_mathml(cls, mathml: str) -> 'Dimension':
        """ this code is brittle and may break if the WikiData MathML representation for dimensions changes """
        tree = etree.XML(mathml)
        no_dim = False
        dims: Dict[str, int] = {}
        for node in tree.xpath('//*[local-name()="mstyle"]/*'):
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


class Quantity(object):
    def __init__(self, identifier: str, label: str):
        self.identifier = identifier
        self.label = label
        self.parents: List['Quantity'] = []
        self.dimension: Optional[Dimension] = None
        self.symbols: List[str] = []

    @property
    def uri(self) -> str:
        return f'https://www.wikidata.org/entity/{self.identifier}'


class Unit(object):
    def __init__(self, identifier: str, label: str):
        self.identifier = identifier
        self.label = label
        self.quantities: List[Quantity] = []
        self.dimension: Optional[Dimension] = None
        self.notations: List[str] = []

    @property
    def uri(self) -> str:
        return f'https://www.wikidata.org/entity/{self.identifier}'


class QuantityWikiData(object):
    def __init__(self):
        pass


class QuantityWikiDataLoader(object):
    def __init__(self, config: Config):
        self.config = config
        self.data: CachedData[QuantityWikiData] = CachedData(self.config, 'quantities-wikidata')

    def get(self) -> QuantityWikiData:
        if self.data.ensured():
            return self.data.data

        quantities: Dict[str, Quantity] = {}
        dim_collection: Dict[str, Dimension] = {}
        with self.load_csv('quantities', ['quantity', 'quantityLabel', 'dimension']) as quantities_reader:
            for quantity, quantityLabel, dimension in quantities_reader:
                identifier = quantity.split('/')[-1]
                new_quant = Quantity(identifier, quantityLabel)
                if dimension.strip():
                    real_dim = Dimension.from_wikidata_mathml(dimension)
                    # idea: only one object per dimension to make pickle dump smaller
                    if str(real_dim) in dim_collection:
                        real_dim = dim_collection[str(real_dim)]
                    else:
                        dim_collection[str(real_dim)] = real_dim
                    new_quant.dimension = real_dim
                quantities[quantity] = new_quant
        # print(quantities.keys())

        units: Dict[str, Unit] = {}
        with self.load_csv('units', ['unit', 'unitLabel', 'quantity', 'SIconversion', 'standardConversion', 'notation']) as units_reader:
            for unit_uri, unitLabel, quantity, si_conversion, standard_conversion, notation in units_reader:
                identifier = unit_uri.split('/')[-1]
                if identifier not in units:
                    units[identifier] = Unit(identifier, unitLabel)
                unit = units[identifier]
                if quantity.strip():
                    if quantity in quantities:
                        quant = quantities[quantity]
                        if quant not in unit.quantities:
                            unit.quantities.append(quant)

        # print(f'Found {len(quantities)} quantities')

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
