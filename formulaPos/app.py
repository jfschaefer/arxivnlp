from flask import Flask, request

app = Flask(__name__)


@app.route('/getAnnotations/<doc_id>')
def getAnnot(doc_id):
    with open(f'annotations/{doc_id}.json') as f:
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
        new_string = '<script src="/static/anno.js"></script>\n</html>'
        s = s.replace('</html>', new_string)
    return s
