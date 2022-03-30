import sys

from lxml import etree

from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager
from arxivnlp.data.dnm import DEFAULT_DNM_CONFIG, DnmRange
from arxivnlp.examples.quantities.center import QuantityCenter
from arxivnlp.examples.quantities.quantity_kb import QuantityKb
from arxivnlp.examples.quantities.wikidata import QuantityWikiDataLoader

CSS = '''
.arxivnlpmessage {
  display: none;
  position: absolute;
  background-color: #ddddaa;
  border-style: solid;
  border-color: #330000;
  padding: 10px;
  font-size: 24pt;
}

.arxivnlpmessagemarker:hover + .arxivnlpmessage {
  display: block;
}

.arxivnlpmessagemarker {
  font-weight: bold;
  font-size: 150%;
  color: red;
}
'''


def main():
    arxivid = sys.argv[1]

    config = Config.get()
    data = QuantityWikiDataLoader(config).get()
    data_manager = DataManager(config)
    quantity_kb = QuantityKb.from_wikidata(data)
    quantity_center = QuantityCenter(data_manager, quantity_kb)

    dnm = data_manager.load_dnm(arxivid, DEFAULT_DNM_CONFIG)
    count = 0
    for occurrence in quantity_center.load_occurrences(arxivid):
        count += 1
        dnm_range = DnmRange.from_string(occurrence.dnm_range, dnm.tree)
        star = '*'
        message = ''
        if occurrence.amount_val is not None:
            message += str(occurrence.amount_val) + ' '
        message += quantity_kb.all_units[occurrence.unit_id].display_name
        dnm.add_node(etree.XML(f'<span><span class="arxivnlpmessagemarker">{star}</span><span class="arxivnlpmessage">{message}</span></span>'),
                     dnm.dnm_point_to_pos(dnm_range.to)[0], after=True)
    dnm.insert_added_nodes()
    dnm.tree.xpath('.//head')[0].append(etree.XML(f'<style>{CSS}</style>'))  # TODO: Escape CSS
    dnm.tree.xpath('.//head')[0].append(etree.XML('<link rel="stylesheet" href="https://ar5iv.labs.arxiv.org/assets/ar5iv.0.7.4.min.css" />'))

    print(f'Annotated {count} occurrences')

    with open('/tmp/annotated.html', 'wb') as fp:
        dnm.tree.write(fp)


if __name__ == '__main__':
    main()
