from lxml import etree

class Document(object):
    def __init__(self, tree: etree.ElementTree, skipped_nodes):
        self.tree = tree
        self.stream = []
        self.skipped_nodes = skipped_nodes
        self.append_to_stream(tree.getroot())

    def append_to_stream(self, node):
        if node.tag not in self.skipped_nodes:
            self.stream.append(node.text)
            for child in node:
                self.append_to_stream(child)
                self.stream.append(child.tail)


