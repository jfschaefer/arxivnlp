from lxml import etree
from arxivnlp.data import datamanager
from arxivnlp.args import auto

auto()
html_parser = etree.HTMLParser()
dm = datamanager.DataManager()

count = 0
count_docs = 0
count_units = 0
doc_ids_with_units = []
with open('docs_with_units.txt', 'w') as f:
    f.write('doc_id, number of units\n')
    for doc_id in dm.arxiv_categories.doc_to_cats:
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
                doc_ids_with_units.append(doc_id)
                f.write(doc_id + ', ' + str(len(all_units)) + '\n')
                print(all_units)
            count_units += len(all_units)

print('doc_ids: ', doc_ids_with_units)

