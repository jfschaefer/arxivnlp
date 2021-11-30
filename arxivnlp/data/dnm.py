from typing import Set, List
from lxml import etree


class DnmConfig(object):
    def __init__(self, nodes_to_skip: Set[str], classes_to_skip: Set[str]):
        self.nodes_to_skip = nodes_to_skip
        self.classes_to_skip = classes_to_skip

    def skip_node(self, node: etree.Element) -> bool:
        classes_of_node = node.get('class')
        if classes_of_node is not None:
            classes_of_node = classes_of_node.split()
            for e in classes_of_node:
                if e in self.classes_to_skip:
                    return True
        if node.tag in self.nodes_to_skip:
            return True
        return False


class StringToken(object):
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
            self.backref_node.addnext(node)     # add a new sibling and move tail behind
            self.backref_node.tail = node.tail[:pos]
            node.tail = node.tail[pos:]
        else:
            raise Exception(f'Unsupported backref type {self.backref_type}')


class Dnm(object):
    def __init__(self, tree: etree.ElementTree, dnm_config: DnmConfig):
        self.tree = tree
        self.tokens: List[StringToken] = []
        self.dnm_config = dnm_config
        self.append_to_stream(tree.getroot())

    def append_to_stream(self, node: etree.Element):
        if not self.dnm_config.skip_node(node):
            self.tokens.append(StringToken(content=node.text, backref_node=node, backref_type='text'))
            for child in node:
                self.append_to_stream(child)
                self.tokens.append(StringToken(content=child.tail, backref_node=child, backref_type='tail'))
