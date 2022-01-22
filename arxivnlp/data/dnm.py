from typing import Set, List, Tuple, Dict, Optional

from lxml import etree


def get_node_classes(node: etree.Element) -> List[str]:
    classes_of_node = node.get('class')
    if classes_of_node is None:
        return []
    else:
        return classes_of_node.split()


class DnmConfig(object):
    def __init__(self, nodes_to_skip: Set[str], classes_to_skip: Set[str], nodes_to_replace: Dict[str, str],
                 classes_to_replace: Dict[str, str]):
        self.nodes_to_skip = nodes_to_skip
        self.classes_to_skip = classes_to_skip
        self.nodes_to_replace = nodes_to_replace
        self.classes_to_replace = classes_to_replace

    def skip_node(self, node: etree.Element) -> bool:
        for e in get_node_classes(node):
            if e in self.classes_to_skip:
                return True
        if node.tag in self.nodes_to_skip:
            return True
        return False

    def replace_node(self, node: etree.Element) -> Optional[str]:
        if node.tag in self.nodes_to_replace:
            return self.nodes_to_replace[node.tag]
        for e in get_node_classes(node):
            if e in self.classes_to_replace:
                return self.classes_to_replace[e]


class Token(object):
    def get_string(self) -> str:
        raise NotImplemented

    def insert_node(self, node: etree.Element, pos: int, after: bool = False):
        raise NotImplemented

    def get_surrounding_node(self) -> etree.Element:
        raise NotImplemented


class StringToken(Token):
    def __init__(self, content: str, backref_node: etree.Element, backref_type: str):
        self.content = content
        self.backref_node = backref_node
        self.backref_type = backref_type

    def get_string(self) -> str:
        return self.content

    def insert_node(self, node: etree.Element, pos: int, after: bool = False):
        if after:
            pos += 1
        if self.backref_type == 'text':
            self.backref_node.insert(0, node)  # 0 means child no. 0
            node.tail = self.backref_node.text[pos:]
            self.backref_node.text = self.backref_node.text[:pos]
        elif self.backref_type == 'tail':
            self.backref_node.addnext(node)  # add a new sibling and move tail behind
            self.backref_node.tail = node.tail[:pos]
            node.tail = node.tail[pos:]
        else:
            raise Exception(f'Unsupported backref type {self.backref_type}')

    def get_surrounding_node(self) -> etree.Element:
        if self.backref_type == 'text':
            return self.backref_node
        elif self.backref_type == 'tail':
            return self.backref_node.getparent()
        else:
            raise Exception(f'Unsupported backref type {self.backref_type}')


class NodeToken(Token):
    def __init__(self, backref_node: etree.Element, replaced_string: str):
        self.backref_node = backref_node
        self.replaced_string = replaced_string

    def get_string(self) -> str:
        return self.replaced_string

    def insert_node(self, node: etree.Element, pos: int, after: bool = False):
        if after:
            self.backref_node.addnext(node)
        else:
            self.backref_node.addprevious(node)

    def get_surrounding_node(self) -> etree.Element:
        return self.backref_node


class Dnm(object):
    def __init__(self, tree: etree.ElementTree, dnm_config: DnmConfig):
        self.tree = tree
        self.dnm_config = dnm_config
        self.is_clean: bool = True  # backrefs are still consistent with tree

        self.tokens: List[Token] = []
        self._append_to_tokens(tree.getroot())
        result = self.generate_string()
        self.string: str = result[0]
        self.backrefs: List[Tuple[Token, int]] = result[1]

        self.nodes_to_add: List[Tuple[etree.Element, int, bool]] = []

    def _append_to_tokens(self, node: etree.Element):
        if not self.dnm_config.skip_node(node):
            replacement = self.dnm_config.replace_node(node)
            if replacement is not None:
                self.tokens.append(NodeToken(backref_node=node, replaced_string=replacement))
            else:
                if node.text:
                    self.tokens.append(StringToken(content=node.text, backref_node=node, backref_type='text'))
                for child in node:
                    self._append_to_tokens(child)
                    if child.tail:
                        self.tokens.append(StringToken(content=child.tail, backref_node=child, backref_type='tail'))

    def generate_string(self) -> Tuple[str, List[Tuple[Token, int]]]:
        string = ''
        backrefs = []
        for token in self.tokens:
            string += token.get_string()
            backrefs.extend([(token, pos) for pos in range(len(token.get_string()))])
        return string, backrefs

    def add_node(self, node: etree.Element, pos: int, after: bool = False):
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
        l.sort(key=lambda e: (-e[1][1], -int(e[1][2]), -e[0] if isinstance(self.backrefs[e[1][1]][0], StringToken) and not e[1][2] else e[0]))
        for node, pos, after in (e[1] for e in l):
            token, pos_relative = self.backrefs[pos]
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

    def get_node(self, pos: int) -> etree.Element:
        return self.dnm.backrefs[self.backrefs[pos]][0].get_surrounding_node()

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
