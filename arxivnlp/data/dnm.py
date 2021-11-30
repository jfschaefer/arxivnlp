from typing import Set
from lxml import etree


class DnmConfig(object):
    def __init__(self, nodes_to_skip: Set[str], classes_to_skip: Set[str]):
        self.nodes_to_skip = nodes_to_skip
        self.classes_to_skip = classes_to_skip

    def skip_node(self, node) -> bool:
        classes_of_node = node.get('class')
        if classes_of_node is not None:
            classes_of_node = classes_of_node.split()
            for e in classes_of_node:
                if e in self.classes_to_skip:
                    return True
        if node.tag in self.nodes_to_skip:
            return True
        return False


class Dnm(object):
    def __init__(self, tree: etree.ElementTree, dnm_config: DnmConfig):
        self.tree = tree
        self.stream = []
        self.dnm_config = dnm_config
        self.append_to_stream(tree.getroot())


    def append_to_stream(self, node):
        if not self.dnm_config.skip_node(node):
            self.stream.append(node.text)
            for child in node:
                self.append_to_stream(child)
                self.stream.append(child.tail)
