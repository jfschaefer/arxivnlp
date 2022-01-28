from lxml import etree
from pathlib import Path
from arxivnlp.data import datamanager
from arxivnlp.args import auto

auto()
# folder = Path('/media/varvara/externalA/arXMLiv_mini/2008')
html_parser = etree.HTMLParser()
dm = datamanager.DataManager()
cats = dm.arxiv_categories.doc_to_cats['1608.05390']
# print(cats)
doc_ids = []
for category in dm.arxiv_categories.cat_to_docs:
    if category.startswith('astro-ph.'):
        doc_ids += dm.arxiv_categories.cat_to_docs[category]
print(len(doc_ids))

count = 0
count_docs = 0
count_units = 0
units = {'second','meter','kilogram'}
for doc_id in doc_ids:
    # print(doc_id)
    if doc_id.startswith('2008'):
        path = dm.locate_doc(doc_id)
        if not path.is_file():
            continue
        count += 1
        if count % 50 == 0:
            print(count, 'count_docs: ', count_docs, 'count_units: ', count_units)
        tree = etree.parse(str(path), html_parser)
        all_units = tree.xpath('//mi[@class="ltx_unit"]/text()')
        if all_units:
            count_docs += 1
            print(all_units)
        count_units += len(all_units)

        # for s in symbols:
        #     if s in units:
        #         print(path)
        #         print(symbols)
        #         break
