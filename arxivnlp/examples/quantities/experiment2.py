import arxivnlp.args
from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager
from arxivnlp.examples.quantities.quantity_kb import QuantityKb
from arxivnlp.examples.quantities.wikidata import QuantityWikiDataLoader

arxivnlp.args.auto()
config = Config.get()
data = QuantityWikiDataLoader(config).get()
data_manager = DataManager(config)

quantity_kb = QuantityKb.from_wikidata(data)
