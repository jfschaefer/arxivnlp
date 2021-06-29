from lxml import etree
import time



class Document(object):
    def __init__(self, tree, keepbackrefs = False):
        self.tree = tree
        self.formulae = []
        self.keepbackrefs = keepbackrefs
        # Types of backrefs:
        #     (n, <node>)     corresponds to entire node
        #     (ns, <node>)    corresponds to start of node
        #     (ne, <node>)    corresponds to end of node
        #     (t, <node>, i)  corresponds to i-th character of node.text
        #     (tt, <node>, i) corresponds to i-th character of node.tail
        self.backrefs = [] if keepbackrefs else None
        self.string = ''
        self.initial_extraction(tree.getroot())

    def push_const(self, s, br):
        self.string += s
        if self.keepbackrefs:
            self.backrefs += [br] * len(s)

    def initial_extraction(self, node):
        # before
        class_val = node.get('class')
        classes = class_val.split() if class_val else []
        recurse = False
        if node.tag == 'math':
            self.push_const(f'@FORMULA{len(self.formulae)}@', ('n', node))
            self.formulae.append(node)
        elif node.tag == 'cite':
            self.push_const(f'@CITATION@', ('n', node))
        elif node.tag in {'h1','h2','h3','h4','h5','h6'}:
            self.push_const(f'@HEADER_START@', ('ns', node))
            recurse = True
        elif any(c in {'ltx_bibliography', 'ltx_page_footer'} for c in classes):
            pass
        else:
            recurse = True

        if recurse:
            if node.text:
                self.string += node.text
                if self.keepbackrefs:
                    self.backrefs += [('t', node, i) for i in range(len(node.text))]
            for child in node:
                self.initial_extraction(child)

        # after
        if node.tag in {'h1','h2','h3','h4','h5','h6'}:
            self.push_const(f'@HEADER_END@', ('ne', node))

        # tail
        if node.tail:
            self.string += node.tail
            if self.keepbackrefs:
                self.backrefs += [('tt', node, i) for i in range(len(node.tail))]


# def recurse(node):
#     if node.tag == 'math':
#         s = 'FORMULA'
#     elif node.tag == 'cite':
#         s = 'CITATION'
#     elif node.get('class') and any(c in {'ltx_bibliography', 'ltx_page_footer'} for c in node.get('class').split()):
#         s = ''
#     else:   # no special treatment
#         s = ''
#         if node.text:
#             s += node.text
#         for child in node:
#             s += recurse(child)
# 
#     if node.tail:
#         s += node.tail
#     return s


parser = etree.HTMLParser()

file = '/drive/arXMLiv_mini/1608/1608.09016.html'


timea = time.time()
tree = etree.parse(file, parser)
timeb = time.time()
# s = recurse(tree.getroot())
doc = Document(tree, False)
# assert len(doc.backrefs) == len(doc.string)
timec = time.time()

# # remove duplicate spaces
# s2 = ''
# for c in s:
#     if c.isspace() and len(s2) and s2[-1].isspace():
#         continue
#     s2 += c
timed = time.time()

print(timeb-timea)
print(timec-timeb)
print(timed-timec)
