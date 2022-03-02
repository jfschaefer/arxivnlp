from typing import Iterator, List, Optional, Union, Tuple

from lxml.etree import _Element


class LabelTree(object):
    def __init__(self, label: str, node: Optional[_Element], children: List['LabelTree']):
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
    def __init__(self, node: Optional[_Element], label: Optional[str] = None, children: Optional[List['Match']] = None):
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
    def match(self, nodes: List[_Element]) -> Iterator[Tuple[List[Match], List[_Element]]]:
        """ Matches some of the `nodes` and yields pairs (`matches`, `rest`),
            where `matches` is the found matches and `rest` are the remaining nodes that still have to be matched. """
        raise NotImplemented


class NodeMatcher(Matcher):
    def match(self, node: _Element) -> Iterator[Match]:
        raise NotImplemented

    def __pow__(self, label: str) -> 'NodeMatcher':
        """ Add a label the matched note. `**` was chosen due to its precedence """
        return MatcherLabelled(self, label)

    def __truediv__(self, other: Union[SeqMatcher, 'NodeMatcher']) -> 'NodeMatcher':
        """ `self / other` gives a matcher that matches the children with `other`.
            Warning: `/` is left-associative, which is rather counter-intuitive in this case. """
        if isinstance(other, SeqMatcher):
            seq_matcher = other
        elif isinstance(other, NodeMatcher):
            seq_matcher = MatcherSeqAny(other)
        else:
            raise Exception(f'Unsupported object for children: {type(other)}')
        return MatcherNodeWithChildren(self, seq_matcher)


class MatcherSeqConcat(SeqMatcher):
    """ Concatenation of sequence matchers """

    def __init__(self, seq_matchers: List[SeqMatcher]):
        self.seq_matchers = seq_matchers

    def match(self, nodes: List[_Element], matchers: Optional[List[SeqMatcher]] = None) \
            -> Iterator[Tuple[List[Match], List[_Element]]]:
        if matchers is None:
            matchers = self.seq_matchers
        if not matchers:
            yield [], nodes
        for match, remainder in matchers[0].match(nodes):
            if len(matchers) == 1:
                yield match, remainder
            else:
                for submatches, lastremainder in self.match(remainder, matchers[1:]):
                    yield match + submatches, lastremainder


class MatcherNodeAsSeq(SeqMatcher):
    def __init__(self, node_matcher: NodeMatcher):
        self.node_matcher = node_matcher

    def match(self, nodes: List[_Element]) -> Iterator[Tuple[List[Match], List[_Element]]]:
        if not nodes:
            return iter(())
        for match in self.node_matcher.match(nodes[0]):
            yield [match], nodes[1:]


class MatcherSeqAny(SeqMatcher):
    """ Matches a whole sequence if a single element matches the specified node matcher """

    def __init__(self, node_matcher: NodeMatcher):
        self.node_matcher = node_matcher

    def match(self, nodes: List[_Element]) -> Iterator[Tuple[List[Match], List[_Element]]]:
        for node in nodes:
            for match in self.node_matcher.match(node):
                yield [match], []


class MatcherTag(NodeMatcher):
    def __init__(self, tagname: str):
        self.tagname = tagname

    def match(self, node: _Element) -> Iterator[Match]:
        if node.tag == self.tagname:
            yield Match(node)


class MatcherNodeWithChildren(NodeMatcher):
    def __init__(self, node_matcher: NodeMatcher, seq_matcher: SeqMatcher):
        self.node_matcher = node_matcher
        self.seq_matcher = seq_matcher

    def match(self, node: _Element) -> Iterator[Match]:
        for match in self.node_matcher.match(node):
            for submatch, remaining in self.seq_matcher.match(node.getchildren()):
                if not remaining:
                    yield match.with_children(submatch)


class MatcherLabelled(NodeMatcher):
    def __init__(self, node_matcher: NodeMatcher, label: str):
        self.node_matcher = node_matcher
        self.label = label

    def match(self, node: _Element) -> Iterator[Match]:
        for match in self.node_matcher.match(node):
            yield match.with_label(self.label)


# Short hands
def tag(name: str) -> NodeMatcher:
    return MatcherTag(name)


def seq(*matchers: Union[NodeMatcher, SeqMatcher]) -> SeqMatcher:
    return MatcherSeqConcat(
        [MatcherNodeAsSeq(matcher) if isinstance(matcher, NodeMatcher) else matcher for matcher in matchers])
