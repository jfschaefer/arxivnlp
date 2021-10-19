from flask import Flask, request, render_template, jsonify
import os
import random
import json


app = Flask(__name__)

@app.route('/')
def get_annopage():
    with open('config.json') as f:
        config = json.load(f)
    return render_template('para_front_page.html', config=config)

@app.route('/getRandomParagraph')
def get_rparagraph():
    paras = os.listdir('paragraphs')
    filename = random.choice(paras)
    with open(f'paragraphs/{filename}') as f:
        content = f.read()
        p = jsonify({'html':content, 'filename':filename})
    return p

@app.route('/storeAnnos/<par_id>', methods=['PUT'])
def store_annos(par_id):
    data = request.get_data(as_text=True)
    with open(f'annotations/{par_id}.json','w') as f:
        f.write(data)
    return ''  # because the server complains if nothing is returned