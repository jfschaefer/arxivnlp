import os, sys, re, util

rootdir = sys.argv[1]

REGEXES = [
    r' (?P<A_able>[a-z]+able)[ ,.]',                                                # differentiable
    r' (be|is) an? (?P<N_isa1>[a-z]+)\.',                                           # is an integer.
    r' (be|is) an? (?P<N_isa2>[a-z]+) (where|and|if|for) ',                         # is an integer and
    r' an? (?P<N_prep>[a-z]+) (of|on|with|from|for|between) ',                      # a function on
    r' (an?|every|some|the) (?P<N_fis>[a-z]+) @FORMULA[0-9]+@ is ',                 # a function $f$ is
        ]

REGEX = re.compile('(' + ')|('.join(REGEXES) + ')')


FILES = util.find_files(rootdir)

print(f'Found {len(FILES)} files')

from lexiconRecord import Records

RECORDS = Records()


for i in range(len(FILES)):
    if i % 100 == 0:
        print(f'{i}/{len(FILES)}')
    with open(FILES[i], 'r') as fp:
        for match in REGEX.finditer(fp.read()):
            for k in match.groupdict():
                if match.group(k) and '_' in k:
                    type_ = k.split('_')[0]
                    if type_ == 'A':
                        RECORDS.push_A(match.group(k), k)
                    if type_ == 'N':
                        RECORDS.push_N(match.group(k), k)

print('DONE')

import pickle
with open('/tmp/records.dmp', 'wb') as fp:
    pickle.dump(RECORDS, fp)

