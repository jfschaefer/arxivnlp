from collections import Counter
import re


substpattern = re.compile(r' *([().,!:?/]) *')
formulapattern = re.compile(r'@FORMULA[0-9]+@')
def insert_trigrams(counter, line):
    modified = ''     # replace e.g. "@HEADER_START@X" with "@HEADER_START@ X"
    par = True
    for letter in line:
        if letter == '@':
            if par:
                modified += ' @'
            else:
                modified += '@ '
            par = not par
        else:
            modified += letter
    modified = substpattern.sub(r' \1 ', modified)
    modified = formulapattern.sub('MathFormula', modified)
    modified = modified.lower().split()
    counter.update(tuple(modified[i:i+3]) for i in range(len(modified)-2))


def count_trigrams(files):
    counter = Counter()
    for i in range(len(files)):
        if i % 100 == 0:
            print(f'{i}/{len(files)}')
        with open(files[i], 'r') as fp:
            for line in fp:
                insert_trigrams(counter, line)
    return counter


if __name__ == '__main__':
    import util, sys, pickle
    files = util.find_files(sys.argv[1])
    counts = count_trigrams(files)
    
    with open('/tmp/trigrams.dmp', 'wb') as fp:
        pickle.dump(dict(counts), fp)

    print(len(counts), 'trigrams found')

    # with open('/tmp/trigrams.dmp', 'rb') as fp: t = pickle.load(fp)

