"""
    THIS FILE IS CURRENTLY NOT USED!
    (It turned out to be way too inefficient)
"""

import logging
from typing import Optional, Iterable

from rdflib import Graph, URIRef
from rdflib_sqlalchemy.store import SQLAlchemy
from sqlalchemy import create_engine

from ..config import Config


class DocMetaCache(object):
    instance: Optional['DocMetaCache'] = None

    @classmethod
    def get(cls, config: Config) -> 'DocMetaCache':
        if cls.instance is None:
            cls.instance = DocMetaCache(config)
        return cls.instance

    def __init__(self, config: Config):
        # Warning: should generally be used as a singleton
        # self.location = 'sqlite:/' + (config.cache_dir/'document-metadata-cache.db').as_uri()[5:]
        self.location = 'sqlite:///:memory:'
        # self.location = str(config.cache_dir/'document-metadata-cache.db')
        logger = logging.getLogger(__name__)
        logger.info(f'Connecting to {self.location}')
        print(self.location)

        self.config = config
        self.graph: Graph = Graph(SQLAlchemy(engine=create_engine(self.location)))
        self.graph.open(self.location, create=True)

    def check_if_present(self, type_) -> bool:
        """ Checks if metadata is already in the cache """
        return (URIRef('meta:base'), URIRef('p:has-metadata'), URIRef('val:' + type_)) in self.graph

    def set_that_present(self, type_):
        """ Indicate that metadata is in the cache """
        self.insert('meta:base', 'p:has-metadata', 'val:' + type_)
        self.graph.commit()   # just to be sure

    def insert(self, sub: str, pred: str, obj: str):
        self.graph.add((URIRef(sub), URIRef(pred), URIRef(obj)))

    def get_subj(self, pred: str, obj: str) -> Iterable[str]:
        for node in self.graph.subjects(URIRef(pred), URIRef(obj)):
            yield str(node)

    def get_obj(self, subj: str, pred: str) -> Iterable[str]:
        for node in self.graph.objects(URIRef(subj), URIRef(pred)):
            yield str(node)

    def close(self):
        logger = logging.getLogger(__name__)
        logger.info(f'Disconnecting from {self.location}')
        self.graph.close()
