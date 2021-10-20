from flask import Flask, request, render_template, jsonify
import os
import random
import json


app = Flask(__name__)

@app.route('/')
def get_overview():
    annos = os.listdir('annotations')
    paras = []
    for filename in annos:
        filename = filename[:-5]
        with open(f'paragraphs/{filename}') as f:
            par = f.read()
            paras.append((par,filename))
    return render_template('overview.html', paras=paras)

@app.route('/annotate/<filename>')
def annotate_paragraph(filename):
    with open('config.json') as f:
        config = json.load(f)
    return render_template('para_front_page.html', config=config, filename=filename)

@app.route('/annotate')
def get_annopage():
    return annotate_paragraph('random')

@app.route('/getParagraph/<arg>')
def get_paragraph(arg):
    paras = os.listdir('paragraphs')
    annos = set(os.listdir('annotations'))
    if arg == 'random':
        filename = random.choice(paras)
    elif arg == 'unannotated':
        unannos = []
        for filename in paras:
            if filename + '.json' not in annos:
                unannos.append(filename)
        filename = random.choice(unannos)
    elif arg == 'annotated':
        filename = random.choice(list(annos))[:-5]
    else:
        filename = arg
    with open(f'paragraphs/{filename}') as f:
        content = f.read()
    annotations = {}
    if os.path.isfile(f'annotations/{filename}.json'):
        with open(f'annotations/{filename}.json', 'r') as f:
            annotations = json.load(f)
    return jsonify({'html':content, 'filename':filename, 'annotations':annotations})

@app.route('/storeAnnos/<par_id>', methods=['PUT'])
def store_annos(par_id):
    data = request.get_data(as_text=True)
    with open(f'annotations/{par_id}.json','w') as f:
        f.write(data)
    return ''  # because the server complains if nothing is returned
