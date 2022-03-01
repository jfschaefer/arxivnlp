import itertools
from typing import Iterator, List, Optional, Union

from lxml.etree import Element


class LabelTree(object):
    def __init__(self, label: str, node: Optional[Element], children: List['LabelTree']):
        self.label = label
        self.node = node
        self.children = children

    def __getitem__(self, item) -> 'LabelTree':
        if isinstance(item, int):
            return self.children[item]
        elif isinstance(item, str):
            for child in self.children:
                if child.label == item:
                    return child
            raise KeyError(f'No child with label {item}')
        raise Exception(f'Cannot get item {item}')


class Match(object):
    def __init__(self, node: Optional[Element], label: Optional[str] = None, children: Optional[List['Match']] = None):
        self.node = node
        self.label = label
        self.children: List['Match'] = children if children is not None else []

    def with_children(self, children: List['Match']) -> 'Match':
        assert not self.children
        return Match(self.node, self.label, children)

    def with_label(self, label: str) -> 'Match':
        if self.label is None:
            return Match(self.node, label, self.children)
        else:
            return Match(None, label, [self])  # create an "empty" label node

    def to_label_tree(self) -> LabelTree:
        lts = self._to_label_tree()
        if len(lts) != 1:
            return LabelTree('root', self.node, lts)
        else:
            return lts[0]

    def _to_label_tree(self) -> List[LabelTree]:
        child_label_trees = [lt for c in self.children for lt in c._to_label_tree()]
        if self.label is not None:
            return [LabelTree(self.label, self.node, child_label_trees)]
        else:
            return child_label_trees


class Matcher(object):
    pass


class SeqMatcher(Matcher):
    def match(self, nodes: List[Element]) -> Iterator[List[Match]]:
        raise NotImplemented


class NodeMatcher(Matcher):
    def match(self, node: Element) -> Iterator[Match]:
        raise NotImplemented

    def __pow__(self, label: str) -> 'NodeMatcher':  # node ** "label" (** chosen due to its precedence)
        return MatcherLabelled(self, label)

    # unfortunately, there is no suitable right-associative operator
    def __truediv__(self, other: Union[SeqMatcher, List['NodeMatcher'], 'NodeMatcher']) -> 'NodeMatcher':
        if isinstance(other, SeqMatcher):
            seq_matcher = other
        elif isinstance(other, list):
            seq_matcher = MatcherSimpleSeq(other)
        elif isinstance(other, NodeMatcher):
            seq_matcher = MatcherSeqAny(other)
        else:
            raise Exception(f'Unsupported object for children: {type(other)}')
        return MatcherNodeWithChildren(self, seq_matcher)


class MatcherSimpleSeq(SeqMatcher):
    def __init__(self, node_matchers: List[NodeMatcher]):
        self.node_matchers = node_matchers

    def match(self, nodes: List[Element]) -> Iterator[List[Match]]:
        if len(nodes) != len(self.node_matchers):
            return iter(())
        return (list(t) for t in itertools.product(
            *[self.node_matchers[i].match(nodes[i]) for i in range(len(self.node_matchers))]))


class MatcherSeqAny(SeqMatcher):
    def __init__(self, node_matcher: NodeMatcher):
        self.node_matcher = node_matcher

    def match(self, nodes: List[Element]) -> Iterator[List[Match]]:
        for node in nodes:
            for match in self.node_matcher.match(node):
                yield [match]


class MatcherTag(NodeMatcher):
    def __init__(self, tagname: str):
        self.tagname = tagname

    def match(self, node: Element) -> Iterator[Match]:
        if node.tag == self.tagname:
            yield Match(node)


class MatcherNodeWithChildren(NodeMatcher):
    def __init__(self, node_matcher: NodeMatcher, seq_matcher: SeqMatcher):
        self.node_matcher = node_matcher
        self.seq_matcher = seq_matcher

    def match(self, node: Element) -> Iterator[Match]:
        for match in self.node_matcher.match(node):
            for submatch in self.seq_matcher.match(node.getchildren()):
                yield match.with_children(submatch)


class MatcherLabelled(NodeMatcher):
    def __init__(self, node_matcher: NodeMatcher, label: str):
        self.node_matcher = node_matcher
        self.label = label

    def match(self, node: Element) -> Iterator[Match]:
        for match in self.node_matcher.match(node):
            yield match.with_label(self.label)


# Short hands
def tag(name: str) -> NodeMatcher:
    return MatcherTag(name)
