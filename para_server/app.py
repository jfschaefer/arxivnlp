from flask import Flask, request, render_template, jsonify
import os
import random
import json

app = Flask(__name__)


with open('config.json') as f:
    CONFIG = json.load(f)


@app.route('/')
def get_overview():
    anno_dir = CONFIG['annotationsdir']
    anno_files = os.listdir(anno_dir)
    paras = []
    annotations = {}
    for filename in anno_files:
        filename = filename[:-5]
        with open(f'paragraphs/{filename}') as f:
            par = f.read()
            paras.append((par,filename))
        with open(f'{anno_dir}/{filename}.json', 'r') as f:
            j = json.load(f)
            for k in j:
                annotations[f'{filename}:{k}'] = j[k]
    return render_template('overview.html', paras=paras, annotations=json.dumps(annotations), config=CONFIG)

@app.route('/annotate/<filename>')
def annotate_paragraph(filename):
    return render_template('para_front_page.html', config=CONFIG, filename=filename, json=json)

@app.route('/annotate')
def get_annopage():
    return annotate_paragraph('random')

@app.route('/getParagraph/<arg>')
def get_paragraph(arg):
    paras = os.listdir('paragraphs')
    anno_dir = CONFIG['annotationsdir']
    annos = set(os.listdir(anno_dir))
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
    if os.path.isfile(f'{anno_dir}/{filename}.json'):
        with open(f'{anno_dir}/{filename}.json', 'r') as f:
            annotations = json.load(f)
    return jsonify({'html':content, 'filename':filename, 'annotations':annotations})

@app.route('/storeAnnos/<par_id>', methods=['PUT'])
def store_annos(par_id):
    anno_dir = CONFIG['annotationsdir']
    data = request.get_data(as_text=True)
    with open(f'{anno_dir}/{par_id}.json','w') as f:
        f.write(data)
    return ''  # because the server complains if nothing is returned
