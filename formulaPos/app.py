from flask import Flask, request

app = Flask(__name__)


@app.route('/getAnnotations/<doc_id>')
def getAnnot(doc_id):
    with open(f'{doc_id}.json') as f:
        return f.read()

