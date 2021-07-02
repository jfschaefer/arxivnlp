'''
    Runs simple standard tasks.
'''

import extract
import util
import sys, os
import time
from lxml import etree



def generate_plaintext():
    ''' Generates the plaintext of a list of files and stores it in a folder.
    Example call: run.py generate_plaintext *.html path/to/outdir '''
    parser = etree.HTMLParser()
    assert len(sys.argv) > 3
    files = sys.argv[2:-1]
    outfolder = sys.argv[-1]
    start = time.time()
    for i, file in enumerate(files):
        print(f'Processing file {i}/{len(files)}')
        if i > 2:
            now = time.time()
            print('Expected remaining time:', util.format_time((now-start)*(len(files)-i)/i))
        if not file.endswith('.html'):
            print(f'Skipping {file} (doesn\'t end with .html)')

        tree = etree.parse(file, parser)
        doc = extract.Document(tree, False)
        doc.cleanup_whitespace()
        doc.sentence_segmentation()
        with open(os.path.join(outfolder, os.path.basename(file)[:-5] + '.txt'), 'w') as fp:
            fp.write(doc.getString())

def regex_match():
    ''' Returns all matches of a regex.  Concretely, the group with name 't' will be printed.
        Example Call: run.py regex_match '(be|is) an? (?P<t>[a-z]+)\\.' path/to/*.txt '''
    import re
    assert len(sys.argv) > 3
    expr = re.compile(sys.argv[2])
    for file in sys.argv[3:]:
        with open(file, 'r') as fp:
            for match in expr.finditer(fp.read()):
                print(match.group('t'))

if __name__ == '__main__':
    commands = {f.__name__ : f for f in [generate_plaintext, regex_match]}
    a = sys.argv
    if len(a) < 3:
        print('not enough arguments')
        sys.exit(1)
    if a[1] not in commands:
        print(f'unknown command {a[1]}')
        print('Known commands:')
        for command in commands:
            print(command)
        sys.exit(1)
    if a[2] in ['-h', '--help']:
        print(commands[a[1]].__doc__)
        sys.exit(0)

    commands[a[1]]()
