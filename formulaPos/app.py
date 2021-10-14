from flask import Flask, request, render_template
from pathlib import Path
import os
import json
from collections import namedtuple


app = Flask(__name__)


@app.route('/getAnnotations/<doc_id>')
def getAnnot(doc_id):
    path = Path(f'annotations/{doc_id}.json')
    if not path.is_file():
        with open(path,'w') as f:
            f.write('{}')
    with open(path) as f:
        return f.read()

@app.route('/storeAnnotations/<doc_id>', methods=['PUT'])
def storeAnnot(doc_id):
    data = request.get_data(as_text=True)
    with open(f'annotations/{doc_id}.json','w') as f:
        f.write(data)
    return ''  # because the server complains if nothing is returned

@app.route('/document/<doc_id>')
def document(doc_id):
    with open(f'data/{doc_id}.html') as f:
        s = f.read()
        new_string = f'<script> const DOCID="{doc_id}"; </script>\n <script src="/static/anno.js"></script>\n</html>'
        s = s.replace('</html>', new_string)
    return s

@app.route('/')
def show_links():
    files = os.listdir('data')
    docs = []
    Entry = namedtuple('Entry', ['filename','status'])  #kind of a class, better readability
    for filename in files:
        filename = filename[:-5]
        status = check_anno(filename)
        docs.append(Entry(filename=filename,status=status))
    return render_template('front-page.html',data=docs, num_docs=len(files))

def check_anno(doc_id):
    path = Path(f'annotations/{doc_id}.json')
    if not path.is_file():
        status = '0.00%'
    with open(path) as f:
        data = json.load(f)
        if data == {}:
            status = '0.00%'
        else:
            count_U = 0
            for anno in data.values():
                if anno == 'U':
                    count_U += 1
            status = f'{100-100*count_U/len(data):.2f}%'
    return status