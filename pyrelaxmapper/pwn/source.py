# -*- coding: utf-8 -*-
from nltk.corpus import wordnet as wn

from pyrelaxmapper.rlabel import wordnet


# SHOULD create an NLTK and SQL PWN source!
class PWordNet(wordnet.RLWordNet):
    """WordNet WordNet interface."""

    # Constants
    POS = {'v': 1, 'n': 2, 'r': 3, 'a': 4}

    def __init__(self, preload=False):
        # self._session = session
        # self._config = config
        self._version = None
        self._synsets = None
        # self._mappings = None
        self._lunits = None
        # self._reltypes = None
        # self._reltypes_name = None
        self._hypernyms = None
        self._hyponyms = None
        # self._domains = None
        # self._pos = None
        if preload:
            self._require_data('all')

    def __str__(self):
        return self._version

    def __repr__(self):
        return self._version

    def __getstate__(self):
        """Return state values to be pickled."""
        return (self._version, self._synsets, self._lunits,
                self._hypernyms, self._hyponyms)
        # , self._reltypes, self._mappings , self._domains, self._pos

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        (self._version, self._synsets, self._lunits,
         self._hypernyms, self._hyponyms) = state
        # , self._reltypes, self._mappings, self._domains, self._pos

    def open(self):
        """Initializes access to WordNet data."""
        pass

    def close(self):
        """Cleans up after use."""
        pass

    def version(self):
        """WordNet version."""
        self._require_data('version')
        return self._version

    def synset(self, id_, pos=None):
        """Find synset with id."""
        self._require_data('synsets')
        return self._synsets[id_]

    def synsets(self, lemma, pos=None):
        """Return all synsets including given lemma and part of speech."""
        pass

    def hypernyms(self, id_):
        self._require_data('hypernyms')
        return self._hypernyms[id_] if id_ in self._hypernyms else []

    def hyponyms(self, id_):
        self._require_data('hyponyms')
        return self._hyponyms[id_] if id_ in self._hyponyms else []

    def synsets_all(self):
        self._require_data('synsets')
        return self._synsets

    # def mappings(self):
    #     self._require_data('mappings')
    #     return self._mappings

    # def pos(self):
    #     """All POS."""
    #     self._require_data('pos')
    #     return self._pos
    #
    # def domains(self):
    #     """All domains."""
    #     self._require_data('domains')
    #     return self._domains

    # Should take into account pos we want to load.
    # Should hash and then put into dictionary.
    # Should return Synset object which is an adapter to the plWN DB Synset
    # Eventually SHOULD USE load as Models with their mappings! encapsulated in PObjects
    def _require_data(self, names=None):
        """Ensure dataset from names are loaded.

        Parameters
        ----------
        names
            Dataset names to load if not yet loaded.
            'all' to load all
        """
        if not isinstance(names, list):
            names = [names]

        if any(name in ['all'] for name in names) and not self._lunits:
            pos = 2
            # Synsets
            synsets = wn.all_synsets(pos)
            self._synsets = {}
            for synset in synsets:
                self._synsets[synset.name()] = PSynset(self, synset)

        if any(name in ['version', 'all'] for name in names) and not self._version:
            self._version = 'PWN {}'.format(wn.version())


class PSynset(wordnet.RLSynset):
    """WordNet Synset interface.

    Parameters
    ----------
    plwordnet : PWordNet
        PWordNet source.
    nltk_synset : nltk.corpus.reader.wordnet.Synset
        Synset
    lunits: dict
        Synset lexical unit ids
    """

    def __init__(self, plwordnet, nltk_synset):
        self._plwordnet = plwordnet
        self._nltk_synset = nltk_synset
        self._lemmas = []
        for lemma in nltk_synset.lemma():
            self._lemmas.append(PLexicalUnit(lemma))
        self._hypernyms = []
        for hypernym in nltk_synset.hypernyms():
            self._hypernyms[hypernym.name()] = plwordnet.synset(hypernym.name())
        self._hyponyms = []
        for hyponym in nltk_synset.hyponyms():
            self._hyponyms[hyponym.name()] = plwordnet.synset(hyponym.name())
        self._pos = nltk_synset.pos()
        # region, topic, usage domains!!
        self._domain = nltk_synset.topic_domains()

    def id_(self):
        return self._nltk_synset.name()

    def __str__(self):
        return self._nltk_synset.name()

    def __repr__(self):
        return self.__str__()

    def lemma_names(self):
        return [lemma.name() for lemma in self._nltk_synset.lemmas()]

    def lemmas(self):
        return self._nltk_synset.lemmas()

    def pos(self):
        return self._pos

    def domain(self):
        return self._domain

    def hypernyms(self):
        return self._hypernyms

    def hyponyms(self):
        return self._hyponyms


class PLexicalUnit(wordnet.RLLexicalUnit):
    """Relaxtion labeling Lexical Unit interface.

    Parameters
    ----------
    nltk_lemma : nltk.corpus.reader.wordnet.Lemma
    """
    # Consider caching more?
    def __init__(self, nltk_lemma):
        self._nltk_lemma = nltk_lemma

    def id_(self):
        """Return unique lexical unit identifier."""
        return self._nltk_lemma.name()

    def synset(self):
        """Identifier.

        Returns
        -------
        nltk.corpus.reader.wordnet.Synset
        """
        return self._nltk_lemma.synset()

    def __str__(self):
        return self.id_()

    def __repr__(self):
        return self.__str__()

    def lemma(self):
        """Lemma."""
        return self._nltk_lemma.name()

    def pos(self):
        """Part of speech."""
        return self.synset().pos()
