import sys


file = sys.argv[1]

with open(file) as fp:
    words = []
    for word in fp:
        word = word.strip()
        if word:
            words.append(word)

    counts = {}
    for w in words:
        if w in counts:
            counts[w] += 1
        else:
            counts[w] = 1

    # abstract
    for w in counts:
        if counts[w] > 1:
            # print(f'        {w}_Obj : Obj;')
            print(f'        {w}_Obj2 : Obj2;')

    # concrete
    for w in counts:
        if counts[w] > 1:
            # print(f'        {w}_Obj = mkCN (mkN "{w}");')
            print(f'        {w}_Obj2 = mkN2 (mkN "{w}") of_Prep;')
