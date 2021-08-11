
class Records(object):
    def __init__(self):
        self.adjectives = {}
        self.nouns = {}

    def push_A(self, a, k):
        if not a in self.adjectives:
            self.adjectives[a] = []
        self.adjectives[a].append(k)

    def push_N(self, n, k):
        if not n in self.nouns:
            self.nouns[n] = []
        self.nouns[n].append(k)



def load(s = '/tmp/records.dmp'):
    import pickle
    with open('/tmp/records.dmp', 'rb') as fp:
        r = pickle.load(fp)
    return r
