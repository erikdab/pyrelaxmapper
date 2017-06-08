# -*- coding: utf-8 -*-
from plwordnet import queries, files
from rlabel import wordnet


# Could load all, then allow to cache it all into a pickle objects.
class PLWNWordNet(wordnet.WordNet):
    # Constants
    RELATION_TYPES = {'hypernyms': 10}
    POS = {'v': 5, 'n': 6, 'r': 7, 'a': 8}

    """plWordNet WordNet interface."""
    def __init__(self, session, config):
        self._session = session
        self._config = config
        self._version = None
        self._synsets = None
        self._lunits = None
        self._hypernyms = None
        self._hyponyms = None
        self._domains = None
        self._pos = None

    def open(self):
        """Initializes access to WordNet data."""
        pass

    def close(self):
        """Cleans up after use."""
        pass

    def version(self):
        """WordNet version."""
        if not self._version:
            self._version = queries.version(self._session)
        return self._version

    def synset(self, id_, pos=None):
        """Find synset with id."""
        self._require_data(['synsets'])
        return self._synsets[id_]

    def synsets(self, lemma, pos=None):
        """Return all synsets including given lemma and part of speech."""
        pass

    def hypernyms(self, id_, pos=None):
        self._require_data(['hypernyms'])
        return self._hypernyms[id_]

    def hyponyms(self, id_):
        pass

    def synsets_all(self):
        pass

    def pos(self):
        """All POS."""
        if not self._pos:
            with open('pos.txt') as file:
                self._pos = files.load_pos(file)
        return self._pos

    def domains(self):
        """All domains."""
        if not self.domains_:
            with open('domains.txt') as file:
                self._domains = files.load_domains(file)
        return self._domains

    # Need to ensure POS also.
    def _require_data(self, names=None):
        """Ensure dataset from names are loaded."""
        if 'synsets' in names and not self._synsets:
                self._synsets = queries.synsets(self._session)
        if 'hypernyms' in names and not self._hypernyms:
            self._hypernyms = queries.synset_relations(self._session)
        if 'hyponyms' in names and not self._hyponyms:
            self._hyponyms = queries.synsets(self._session)
