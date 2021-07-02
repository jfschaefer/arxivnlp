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
        self.string = ''           # note: might also be list of characters -> use getString
        self.initial_extraction(tree.getroot())
        self.whitespace_normalized = False

    def getString(self):
        if type(self.string) == list:
            self.string = ''.join(self.string)
        return self.string

    def push_const(self, s, br):
        self.string += s
        if self.keepbackrefs:
            self.backrefs += [br] * len(s)

    def initial_extraction(self, node):
        # before
        class_val = node.get('class')
        classes = set(class_val.split()) if class_val else set()
        recurse = False
        if node.tag == 'math' or 'ltx_equationgroup' in classes:
            self.push_const(f'@FORMULA{len(self.formulae)}@', ('n', node))
            self.formulae.append(node)
        elif node.tag == 'cite':
            self.push_const(f'@CITATION@', ('n', node))
        elif node.tag in {'h1','h2','h3','h4','h5','h6'}:
            self.push_const(f'\n@HEADER_START@', ('ns', node))
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
            self.push_const(f'@HEADER_END@\n', ('ne', node))

        # tail
        if node.tail:
            self.string += node.tail
            if self.keepbackrefs:
                self.backrefs += [('tt', node, i) for i in range(len(node.tail))]

    def cleanup_whitespace(self):
        ''' removes leading and trailing white spaces and substitutes consecutive white spaces by a singe space '''
        newchars = []    # according to my tests, joining a list of characters is ~20% faster (and we might not even join it)
        hadspace = False
        if self.keepbackrefs:
            newbackrefs = []
            for i, c in enumerate(self.string):
                if c in {' ', '\n', '\t', '\r'}:   # faster than .isspace()
                    if hadspace:
                        continue
                    newchars.append(' ')
                    hadspace = True
                else:
                    newchars.append(c)
                    hadspace = False
                newbackrefs.append(self.backrefs[i])
            self.backrefs = newbackrefs
        else:
            for c in self.string:
                if c in {' ', '\n', '\t', '\r'}:   # faster than .isspace()
                    if hadspace:
                        continue
                    newchars.append(' ')
                    hadspace = True
                else:
                    newchars.append(c)
                    hadspace = False
        self.string = newchars

        # trim
        if len(self.string) and self.string[0].isspace():
            self.string = self.string[1:]
            if self.keepbackrefs:
                self.backrefs = self.backrefs[1:]
        if len(self.string) and self.string[-1].isspace():
            self.string = self.string[:-1]
            if self.keepbackrefs:
                self.backrefs = self.backrefs[:-1]

        self.whitespace_normalized = True

    def sentence_segmentation(self):
        ''' Fairly rudimentary sentence tokenization. Getting this completely right will be future work. '''
        assert self.whitespace_normalized
        newchars = []

        # helpers
        def follows_token(i, token):
            ''' token coming up in string '''
            return len(self.string) > i + len(token) and self.string[i:i+len(token)] == token
        def token_was(token):
            ''' newchars ended with token '''
            return len(newchars) >= len(token) and all(newchars[i] == token[i] for i in range(-1, -len(token)-1, -1))
        def was_formula():
            if len(newchars) < 6 or newchars[-1] != '@':
                return None
            i = len(newchars) - 2
            number = ''
            while i >= 0 and i > len(newchars) - 20:
                if newchars[i] == 'A':
                    if i < len('@FORMUL'):
                        return None
                    if ''.join(newchars[i-len('@FORMUL'):i]) != '@FORMUL':
                        return None
                    if not number.isdigit():
                        return None
                    return int(number)
                else:
                    number = newchars[i] + number
                    i -= 1
            return None

        for i, c in enumerate(self.string):
            # cover common cases quickly
            # if c not in {' ', '@'}:
            if c != ' ':
                newchars.append(c)
                continue
            if not newchars or newchars[-1] not in {'.', '@', '?', '!'}:
                newchars.append(c)
                continue

            # now to the interesting cases
            if c == ' ':
                if follows_token(i+1, '@HEADER_START@'):
                    newchars.append('\n')
                    continue
                if len(newchars) > 5 and newchars[-1] in {'.', '?', '!'} and len(self.string) > i+1 and \
                            (self.string[i+1].isupper() or \
                            # probably a new sentence
                            self.string[i+1] == '@' and newchars[-3] != '.'):  # probably a new sentence (make sure it wasn't "i.e." etc.)
                    newchars.append('\n')
                    continue
                if len(newchars) and newchars[-1] == '@':
                    if token_was('@HEADER_END@'):
                        newchars.append('\n')
                        continue
                    if len(self.string) > i+1 and self.string[i+1].isupper():
                        f = was_formula()
                        if f is not None:
                            class_val = self.formulae[f].get('class')
                            if class_val and 'ltx_equationgroup' in class_val:
                                newchars.append('\n')
                                continue

            newchars.append(c)
        self.string = newchars

    def insert_node_at_offset(self, offset, node):
        assert self.keepbackrefs
        assert 0 <= offset < len(self.backrefs)
        bf = self.backrefs[offset]
        # TODO: fix backrefs everywhere, fix errors causing from reset of tail/text after insert
        if bf[0] == 'n':
            bf[1].addprevious(node)
        elif bf[0] == 'ns':             # unclear: should it be inside or outside the node?
            node.tail = bf[1].text
            bf[1].text = None
            bf[1].insert(0, node)
        elif bf[0] == 'ne':             # unclear: should it be inside or outside the node?
            # node.tail = bf[1].tail
            bf[1].insert(1, node)
        elif bf[0] == 't':
            node.tail = bf[1].text[bf[2]:]
            bf[1].text = bf[1].text[:bf[2]]
            bf[1].insert(0, node)
            i = offset
            while i < len(self.backrefs):
                bfi = self.backrefs[i]
                if bfi[0] != 't': break
                if bfi[1] != bf[1]: break
                self.backrefs[i] = ('tt', node, bfi[2] - bf[2])
                i += 1
        elif bf[0] == 'tt':
            oldtail = bf[1].tail
            bf[1].addnext(node)
            bf[1].tail = oldtail[:bf[2]]
            node.tail = oldtail[bf[2]:]
            i = offset
            while i < len(self.backrefs):
                bfi = self.backrefs[i]
                if bfi[0] != 'tt': break
                if bfi[1] != bf[1]: break
                self.backrefs[i] = ('tt', node, bfi[2] - bf[2])
                i += 1
        else:
            raise Exception(f'Invalid backref {bf}')
        # Types of backrefs:
        #     (n, <node>)     corresponds to entire node
        #     (ns, <node>)    corresponds to start of node
        #     (ne, <node>)    corresponds to end of node
        #     (t, <node>, i)  corresponds to i-th character of node.text
        #     (tt, <node>, i) corresponds to i-th character of node.tail







if __name__ == '__main__':
    parser = etree.HTMLParser()
    
    file = '/drive/arXMLiv_mini/1608/1608.09016.html'
    
    
    timea = time.time()
    tree = etree.parse(file, parser)
    timeb = time.time()
    # s = recurse(tree.getroot())
    doc = Document(tree, True)
    
    # assert len(doc.backrefs) == len(doc.string)
    timec = time.time()
    print(len(doc.string))
    doc.cleanup_whitespace()
    print(len(doc.string))
    doc.sentence_segmentation()
    # print(doc.getString())
    # # remove duplicate spaces
    # s2 = ''
    # for c in s:
    #     if c.isspace() and len(s2) and s2[-1].isspace():
    #         continue
    #     s2 += c
    timed = time.time()
    
    for i, c in enumerate(doc.string):
        if c == '\n':
            doc.insert_node_at_offset(i, etree.XML('<span>❚</span>'))
    
    with open('/tmp/test.html', 'w', encoding='utf-8') as fp:
        doc.tree.write(fp)
    
    print(timeb-timea)
    print(timec-timeb)
    print(timed-timec)
