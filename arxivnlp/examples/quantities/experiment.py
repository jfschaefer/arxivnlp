import arxivnlp.args
from arxivnlp.config import Config
from arxivnlp.examples.quantities.wikidata import QuantityWikiDataLoader


def main():
    arxivnlp.args.auto()
    data = QuantityWikiDataLoader(Config.get()).get()



if __name__ == '__main__':
    main()
