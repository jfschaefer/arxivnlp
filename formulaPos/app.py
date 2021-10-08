from flask import Flask, request

app = Flask(__name__)


@app.route('/getAnnotations/<doc_id>')
def getAnnot(doc_id):
    with open(f'annotations/{doc_id}.json') as f:
        return f.read()

@app.route('/storeAnnotations/<doc_id>')
def storeAnnot(doc_id):
    data = request.get_data(as_text=True)
    with open(f'annotations/{doc_id}.json','w') as f:
        f.write(data)
    return ''  # because the server complains if nothing is returned

@app.route('/document/<doc_id>')
def document(doc_id):
    with open('modify.js') as m:
        js = m.read()
    with open(f'data/{doc_id}.html') as f:
        s = f.read()
        new_string = f'<script>\n {js} \n </script> \n </html>'
        s = s.replace('</html>', new_string)
    return s