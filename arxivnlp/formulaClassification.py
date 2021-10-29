from lxml import etree

RELATIONAL_OPERATORS: set[str] = {'∈', '∋', '<', '>', '=', '≥', '≤', '⊆', '⊆', '⊂', '⊃'}


def classify(node: etree.Element, insideTable: bool = False) -> str:
    if node.tag == 'math':
        semantics_node = next((c for c in node if c.tag == 'semantics'), None)
        if semantics_node is None:
            return 'U'
        mrow_node = next((c for c in semantics_node if c.tag == 'mrow'), None)
        if mrow_node is None:
            if any(c.tag in {'mi', 'msub', 'msup', 'msubsup'} for c in semantics_node):
                return 'iota'
            if insideTable and any((c.tag == 'mo' and c.text in RELATIONAL_OPERATORS) for c in semantics_node):   # insideTable -> entire table presumably o
                return 'o'
            return 'U'
        mos = [c.text for c in mrow_node if c.tag == 'mo']
        if any((mo in RELATIONAL_OPERATORS) for mo in mos):
            return 'o'
        return 'iota'
    else:
        for child in node:
            d = {}
            _recurse(child, d, True)
            if 'o' in d.values():
                return 'o'
            return 'iota'
        return 'U'


def _recurse(node: etree.Element, tags: dict[str, str], insideTable: bool = False):
    # before
    class_val = node.get('class')
    classes = set(class_val.split()) if class_val else set()
    id = node.get('id')
    if node.tag == 'math' or 'ltx_equationgroup' in classes or ('ltx_equation' in classes and id):
        assert id
        tags[id] = classify(node, insideTable)
    else:
        for child in node:
            _recurse(child, tags, insideTable)

def get_classifications(root: etree.Element) -> dict[str, str]:
    classifications: dict[str, str] = {}
    _recurse(root, classifications)
    return classifications


# classes = set(class_val.split()) if class_val else set()
# recurse = False
# if node.tag == 'math' or 'ltx_equationgroup' in classes or 'ltx_equation' in classes:

if __name__ == '__main__':
    import sys, json
    file = sys.argv[1]
    parser = etree.HTMLParser()
    tree = etree.parse(file, parser)
    classifications = get_classifications(tree.getroot())
    print(json.dumps(classifications))
