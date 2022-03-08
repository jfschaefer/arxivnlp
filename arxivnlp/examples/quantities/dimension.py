from typing import List, Set, Dict, Any

from lxml import etree

from arxivnlp.utils import superscript_int


class Dimension(object):
    # time, length, mass, electirc current, abs. temperature, amount of subst., luminous intensity
    dim_order: List[str] = list('TLMIΘNJ')
    acceptable_dims: Set[str] = set(dim_order)
    unique_instances: Dict[str, 'Dimension'] = {}
    __slots__ = ['dims', 'string']

    def __init__(self, dims: Dict[str, int]):
        assert all(dim in self.acceptable_dims for dim in dims)
        self.dims = dims

        self.string: str = ''
        for d in self.dim_order:
            if d in self.dims and self.dims[d]:
                self.string += f'{d}{superscript_int(self.dims[d])}'
        if not self.string:
            self.string = '1'

    def unique(self) -> 'Dimension':
        return self.unique_instances.setdefault(self.string, self)

    def __str__(self) -> str:
        """ Unique string representation """
        return self.string

    def __eq__(self, other) -> bool:
        return self.string == other.string

    def __neq__(self, other) -> bool:
        return self.string == other.string

    def __hash__(self):
        return hash(self.string)

    @classmethod
    def from_wikidata_mathml(cls, mathml: str) -> 'Dimension':
        """ this code is brittle and may break if the WikiData MathML representation for dimensions changes """
        tree = etree.XML(mathml)
        no_dim = False
        dims: Dict[str, int] = {}
        node: Any
        for node in tree.xpath('//*[local-name()="mstyle"]/*'):  # type: ignore
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