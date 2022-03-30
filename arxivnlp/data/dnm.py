from typing import Set, List, Tuple, Dict, Optional

from lxml.etree import _Element, _ElementTree

from arxivnlp.util import get_node_classes


class DnmPoint(object):
    def __init__(self, node: _Element, text_offset: Optional[int] = None, tail_offset: Optional[int] = None):
        assert text_offset is None or tail_offset is None
        self.node = node
        self.text_offset = text_offset
        self.tail_offset = tail_offset

    def to_string(self) -> str:
        xpath = self.node.getroottree().getpath(self.node)
        if self.text_offset is not None:
            return f'{xpath}+text{self.text_offset}'
        if self.tail_offset is not None:
            return f'{xpath}+tail{self.tail_offset}'
        return xpath

    @classmethod
    def from_string(cls, string: str, root: _ElementTree) -> 'DnmPoint':
        if '+' in string:
            xpath, offset = string.split('+')
            node = root.xpath(xpath)[0]
            if offset.startswith('text'):
                return DnmPoint(node, text_offset=int(offset[4:]))
            else:
                assert offset.startswith('tail')
                return DnmPoint(node, tail_offset=int(offset[4:]))
        return DnmPoint(root.xpath(string)[0])


class DnmRange(object):
    def __init__(self, from_: DnmPoint, to: DnmPoint, right_closed: bool = False):
        self.from_ = from_
        self.to = to
        self.right_closed = right_closed  # `to` is included in range

    def to_string(self) -> str:
        return f'{self.from_.to_string()}&{self.to.to_string()}&{self.right_closed}'

    @classmethod
    def from_string(cls, string: str, root: _ElementTree) -> 'DnmRange':
        x, y, b = string.split('&')
        return DnmRange(DnmPoint.from_string(x, root), DnmPoint.from_string(y, root), {'True': True, 'False': False}[b])


class DnmConfig(object):
    def __init__(self, nodes_to_skip: Set[str], classes_to_skip: Set[str], nodes_to_replace: Dict[str, str],
                 classes_to_replace: Dict[str, str]):
        self.nodes_to_skip = nodes_to_skip
        self.classes_to_skip = classes_to_skip
        self.nodes_to_replace = nodes_to_replace
        self.classes_to_replace = classes_to_replace

    def skip_node(self, node: _Element) -> bool:
        for e in get_node_classes(node):
            if e in self.classes_to_skip:
                return True
        if node.tag in self.nodes_to_skip:
            return True
        return False

    def replace_node(self, node: _Element) -> Optional[str]:
        if node.tag in self.nodes_to_replace:
            return self.nodes_to_replace[node.tag]
        for e in get_node_classes(node):
            if e in self.classes_to_replace:
                return self.classes_to_replace[e]
        return None


class Token(object):
    start_pos_in_dnm: Optional[int] = None

    def get_string(self) -> str:
        raise NotImplemented

    def insert_node(self, node: _Element, pos: int, after: bool = False):
        raise NotImplemented

    def get_surrounding_node(self) -> _Element:
        raise NotImplemented


class StringToken(Token):
    def __init__(self, content: str, backref_node: _Element, backref_type: str):
        self.content = content
        self.backref_node = backref_node
        self.backref_type = backref_type

    def get_string(self) -> str:
        return self.content

    def insert_node(self, node: _Element, pos: int, after: bool = False):
        if after:
            pos += 1
        if self.backref_type == 'text':
            self.backref_node.insert(0, node)  # 0 means child no. 0
            assert self.backref_node.text is not None
            node.tail = self.backref_node.text[pos:]
            self.backref_node.text = self.backref_node.text[:pos]
        elif self.backref_type == 'tail':
            self.backref_node.addnext(node)  # add a new sibling and move tail behind
            assert node.tail is not None
            self.backref_node.tail = node.tail[:pos]
            node.tail = node.tail[pos:]
        else:
            raise Exception(f'Unsupported backref type {self.backref_type}')

    def get_surrounding_node(self) -> _Element:
        if self.backref_type == 'text':
            return self.backref_node
        elif self.backref_type == 'tail':
            parent = self.backref_node.getparent()
            assert parent is not None
            return parent
        else:
            raise Exception(f'Unsupported backref type {self.backref_type}')


class NodeToken(Token):
    def __init__(self, backref_node: _Element, replaced_string: str):
        self.backref_node = backref_node
        self.replaced_string = replaced_string

    def get_string(self) -> str:
        return self.replaced_string

    def insert_node(self, node: _Element, pos: int, after: bool = False):
        if after:
            self.backref_node.addnext(node)
        else:
            self.backref_node.addprevious(node)

    def get_surrounding_node(self) -> _Element:
        return self.backref_node


class Dnm(object):
    def __init__(self, tree: _ElementTree, dnm_config: DnmConfig):
        self.tree = tree
        self.dnm_config = dnm_config
        self.is_clean: bool = True  # backrefs are still consistent with tree

        self.tokens: List[Token] = []
        self.node_to_token_range: Dict[_Element, Tuple[int, int]] = {}
        self.node_to_text_token: Dict[_Element, StringToken] = {}
        self.node_to_tail_token: Dict[_Element, StringToken] = {}
        self._append_to_tokens(tree.getroot())
        self.string: str = ''
        self.backrefs_token: List[Token] = []
        self.backrefs_pos: List[int] = []
        self.string = ''.join(token.get_string() for token in self.tokens)
        self.backrefs_token = []
        self.backrefs_pos = []
        for token in self.tokens:
            token.start_pos_in_dnm = len(self.backrefs_token)
            for pos in range(len(token.get_string())):
                self.backrefs_token.append(token)
                self.backrefs_pos.append(pos)

        self.nodes_to_add: List[Tuple[_Element, int, bool]] = []

    def dnm_point_to_pos(self, point: DnmPoint) -> Tuple[int, Optional[int]]:
        if point.tail_offset is not None:
            if point.node in self.node_to_tail_token:
                return self.node_to_tail_token[point.node].start_pos_in_dnm + point.tail_offset, None
        if point.text_offset is not None:
            if point.node in self.node_to_text_token:
                return self.node_to_text_token[point.node].start_pos_in_dnm + point.text_offset, None
        if point.node in self.node_to_token_range:
            start, end = self.node_to_token_range[point.node]
            start_offset = self.tokens[start].start_pos_in_dnm
            end_token = self.tokens[end]
            if isinstance(end_token, StringToken) and end_token.backref_type == 'tail':
                return start_offset, end_token.start_pos_in_dnm
            if end + 1 < len(self.tokens):
                return start_offset, self.tokens[end + 1].start_pos_in_dnm
            return start_offset, len(self.string)
        return self.dnm_point_to_pos(DnmPoint(point.node.getparent()))  # ignore tail/text

    def get_dnm_point(self, pos: int) -> DnmPoint:
        token = self.backrefs_token[pos]
        rel_pos = self.backrefs_pos[pos]
        if isinstance(token, StringToken):
            if token.backref_type == 'text':
                return DnmPoint(token.backref_node, text_offset=rel_pos)
            assert token.backref_type == 'tail'
            return DnmPoint(token.backref_node, tail_offset=rel_pos)
        assert isinstance(token, NodeToken)
        return DnmPoint(token.backref_node)

    def _append_to_tokens(self, node: _Element):
        if not self.dnm_config.skip_node(node):
            start_range = len(self.tokens)
            replacement = self.dnm_config.replace_node(node)
            if replacement is not None:
                self.tokens.append(NodeToken(backref_node=node, replaced_string=replacement))
            else:
                if node.text:
                    token = StringToken(content=node.text, backref_node=node, backref_type='text')
                    self.tokens.append(token)
                    self.node_to_text_token[node] = token
                for child in node:
                    self._append_to_tokens(child)
                    if child.tail:
                        token = StringToken(content=child.tail, backref_node=child, backref_type='tail')
                        self.tokens.append(token)
                        self.node_to_tail_token[child] = token
            self.node_to_token_range[node] = (start_range, len(self.tokens))

    def add_node(self, node: _Element, pos: int, after: bool = False):
        self.nodes_to_add.append((node, pos, after))

    def insert_added_nodes(self, ignore_is_clean: bool = False):
        if (not self.is_clean) and not ignore_is_clean:
            raise Exception('Nodes have already been added to the tree and some back references may be wrong. '
                            'Adding new nodes can lead to undefined behaviour')
        if self.nodes_to_add:
            self.is_clean = False
        l = list(enumerate(self.nodes_to_add))
        # Sorting strategy:
        # 1. from back to front
        # 2. first after
        # 3. prefer the ones inserted first, unless it is a string token (and not after)
        l.sort(key=lambda e: (-e[1][1], -int(e[1][2]),
                              -e[0] if isinstance(self.backrefs_token[e[1][1]], StringToken) and not e[1][2] else e[0]))
        for node, pos, after in (e[1] for e in l):
            token, pos_relative = self.backrefs_token[pos], self.backrefs_pos[pos]
            token.insert_node(node, pos_relative, after)
        self.nodes_to_add = []

    def get_full_dnmstr(self) -> 'DnmStr':
        return DnmStr(self.string, backrefs=list(range(len(self.string))), dnm=self)


class DnmStr(object):
    def __init__(self, string: str, backrefs: List[int], dnm: Dnm):
        assert len(string) == len(backrefs)
        self.string = string
        self.backrefs = backrefs
        self.dnm = dnm

    def __len__(self):
        return len(self.string)

    def __getitem__(self, item) -> 'DnmStr':
        backrefs = [self.backrefs[item]] if isinstance(item, int) else self.backrefs[item]
        return DnmStr(string=self.string[item], backrefs=backrefs, dnm=self.dnm)

    def __repr__(self):
        return f'SubString({repr(self.string)})'

    def get_node(self, pos: int) -> _Element:
        return self.dnm.backrefs_token[self.backrefs[pos]].get_surrounding_node()

    def strip(self) -> 'DnmStr':
        str_start = 0
        str_end = 0
        for i in range(len(self.string)):
            if not self.string[i].isspace():
                str_start = i
                break
        for i in range(len(self.string) - 1, -1, -1):
            if not self.string[i].isspace():
                str_end = i + 1
                break
        return self[str_start:str_end]

    def normalize_spaces(self) -> 'DnmStr':
        new_string = ''
        new_backrefs = []
        for i in range(len(self)):
            if not self.string[i].isspace():
                new_string += self.string[i]
                new_backrefs.append(self.backrefs[i])
            else:
                if not (i >= 1 and self.string[i - 1].isspace()):
                    new_string += ' '
                    new_backrefs.append(self.backrefs[i])
        return DnmStr(string=new_string, backrefs=new_backrefs, dnm=self.dnm)


DEFAULT_DNM_CONFIG = DnmConfig(nodes_to_skip={'head', 'figure'},
                               classes_to_skip={'ltx_bibliography', 'ltx_page_footer', 'ltx_dates', 'ltx_authors',
                                                'ltx_role_affiliationtext', 'ltx_tag_equation', 'ltx_classification',
                                                'ltx_tag_section', 'ltx_tag_subsection'},
                               nodes_to_replace={'math': 'MathNode'},
                               classes_to_replace={'ltx_equationgroup': 'MathGroup', 'ltx_cite': 'LtxCite',
                                                   'ltx_ref': 'LtxRef', 'ltx_ref_tag': 'LtxRef',
                                                   'ltx_equation': 'MathEquation'})

EMPTY_DNM_CONFIG = DnmConfig(nodes_to_skip=set(), classes_to_skip=set(), nodes_to_replace={}, classes_to_replace={})
