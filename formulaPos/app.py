from flask import Flask, request
from pathlib import Path

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
