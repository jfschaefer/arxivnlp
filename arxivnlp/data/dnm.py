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

    def insert_node(self, node: etree.Element, pos: int):
        raise NotImplemented


class StringToken(Token):
    def __init__(self, content: str, backref_node: etree.Element, backref_type: str):
        self.content = content
        self.backref_node = backref_node
        self.backref_type = backref_type

    def get_string(self) -> str:
        return self.content

    def insert_node(self, node: etree.Element, pos: int):
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


class NodeToken(Token):
    def __init__(self, backref_node: etree.Element, replaced_string: str):
        self.backref_node = backref_node
        self.replaced_string = replaced_string

    def get_string(self) -> str:
        return self.replaced_string

    def insert_node(self, node: etree.Element, pos: int):
        self.backref_node.addprevious(node)


class Dnm(object):
    def __init__(self, tree: etree.ElementTree, dnm_config: DnmConfig):
        self.tree = tree
        self.tokens: List[Token] = []
        self.dnm_config = dnm_config
        self.append_to_stream(tree.getroot())
        result = self.generate_string()
        self.string: str = result[0]
        self.backrefs: List[Tuple[Token, int]] = result[1]

    def append_to_stream(self, node: etree.Element):
        if not self.dnm_config.skip_node(node):
            replacement = self.dnm_config.replace_node(node)
            if replacement is not None:
                self.tokens.append(NodeToken(backref_node=node, replaced_string=replacement))
            else:
                if node.text:
                    self.tokens.append(StringToken(content=node.text, backref_node=node, backref_type='text'))
                for child in node:
                    self.append_to_stream(child)
                    if child.tail:
                        self.tokens.append(StringToken(content=child.tail, backref_node=child, backref_type='tail'))

    def generate_string(self) -> Tuple[str, List[Tuple[Token, int]]]:
        string = ''
        backrefs = []
        for token in self.tokens:
            string += token.get_string()
            backrefs.extend([(token, pos) for pos in range(len(token.get_string()))])
        return string, backrefs

    def insert_node(self, node: etree.Element, pos: int):
        token, pos_relative = self.backrefs[pos]
        token.insert_node(node, pos_relative)


DEFAULT_DNM_CONFIG = DnmConfig(nodes_to_skip={'head', 'figure'},
                               classes_to_skip={'ltx_bibliography', 'ltx_page_footer', 'ltx_dates', 'ltx_authors',
                                                'ltx_role_affiliationtext', 'ltx_tag_equation', 'ltx_classification'},
                               nodes_to_replace={'math': 'MathNode'},
                               classes_to_replace={'ltx_equationgroup': 'MathGroup', 'ltx_cite': 'LtxCite',
                                                   'ltx_ref': 'LtxRef', 'ltx_ref_tag': 'LtxRef'})
