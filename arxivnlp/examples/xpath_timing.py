import time
from typing import Any

from lxml import etree
from lxml.etree import _Element

from arxivnlp.config import Config
from arxivnlp.data.datamanager import DataManager
from arxivnlp.data.dnm import Dnm, DEFAULT_DNM_CONFIG

datamanager = DataManager(Config.get())
with datamanager.arxmliv_docs.open('2007.08392') as fpin:
    parser: Any = etree.HTMLParser()
    start = time.time()
    tree = etree.parse(fpin, parser)
    print('parse time:', time.time() - start)

    start = time.time()
    for i in range(100):
        e = tree.xpath('//*[@id="S12.SS3.p15.1.m1.1"]')
        assert e
    print('xpath1 time', (time.time() - start)/100)

    start = time.time()
    for i in range(1000):
        better_xpath = tree.getpath(e[0])
    print('xpath2 gen. time', (time.time() - start)/1000)


    print('xpath2:', better_xpath)
    start = time.time()
    for i in range(1000):
        e2 = tree.xpath(better_xpath)
    print('xpath2 time', (time.time() - start)/1000)

    # dnm gen
    start = time.time()
    dnm = Dnm(tree, DEFAULT_DNM_CONFIG)
    print('dnm gen tim', (time.time() - start))
    print(len(dnm.string))
