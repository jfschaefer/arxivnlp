from typing import List

from lxml.etree import _Element


def get_node_classes(node: _Element) -> List[str]:
    classes_of_node = node.get('class')
    if classes_of_node is None:
        return []
    else:
        return classes_of_node.split()
