# -*- coding: utf-8 -*-
from nltk.corpus import wordnet as wn

from pyrelaxmapper.wnmap import wnsource


# SHOULD create an NLTK and SQL PWN source!
class PWordNet(wnsource.RLWordNet):
    """WordNet WordNet interface."""
    POS = {'v': 1, 'n': 2, 'r': 3, 'a': 4}

    def __init__(self):
        # self._config = config
        self._version = None
        self._synsets = None
        self._load_data()

    def version(self):
        return self._version

    def synset(self, id_):
        return self._synsets[id_]

    def synsets(self, lemma, pos=None):
        pass

    def synsets_all(self):
        return self._synsets

    # Should take into account pos we want to load.
    # Should hash and then put into dictionary.
    # Should return Synset object which is an adapter to the plWN DB Synset
    # Eventually SHOULD USE load as Models with their mappings! encapsulated in PObjects
    def _load_data(self):
        """Ensure dataset from names are loaded.

        Parameters
        ----------
        names
            Dataset names to load if not yet loaded.
            'all' to load all
        """
        if not self._synsets:
            pos = 'n'
            synsets = wn.all_synsets(pos)
            self._synsets = {}
            for synset in synsets:
                self._synsets[synset.name()] = PSynset(self, synset)

            # TODO: Pickling error? Too much recursion
            # Maybe restore links after loading from pickle?
            # Update hyper/hipo references
            # for synset in self._synsets.values():
            #     synset.update_rels(self)

        if not self._version:
            self._version = 'PWN {}'.format(wn.get_version())


class PSynset(wnsource.RLSynset):
    """WordNet Synset interface.

    Parameters
    ----------
    pwordnet : PWordNet
    nltk_synset : nltk.corpus.reader.wordnet.Synset
        Synset
    """

    def __init__(self, pwordnet,  nltk_synset):
        self._pwordnet = pwordnet
        self._id = nltk_synset.name()
        self._name = nltk_synset.name()
        self._pos = nltk_synset.pos()
        # nltk.lexname() 'noun.animal'!!
        self._lemmas = []
        for lemma in nltk_synset.lemmas():
            self._lemmas.append(PLexicalUnit(self._name, lemma.name(), self._pos))
        self._hypernyms = [syn.name() for syn in nltk_synset.hypernyms()]
        self._hypernym_paths = []
        for path in nltk_synset.hypernym_paths():
            self._hypernym_paths.append([syn.name() for syn in path])
        self._hyponyms = [syn.name() for syn in nltk_synset.hyponyms()]
        # self._hypernyms = []
        # self._hypernym_paths = []
        # self._hyponyms = []

    def id_(self):
        return self._id

    def name(self):
        return self._name

    def update_rels(self, pwordnet):
        """Update relation links (reference)."""
        old = self._hypernyms
        self._hypernyms = []
        for hypernym in old:
            self._hypernyms.append(pwordnet.synset(hypernym))
        old = self._hyponyms
        self._hyponyms = []
        for hyponym in old:
            self._hyponyms.append(pwordnet.synset(hyponym))
        old = self._hypernym_paths
        self._hypernym_paths = []
        for hypernym_path in old:
            path = []
            for hypernym in hypernym_path:
                path.append(pwordnet.synset(hypernym.name()))
            self._hypernym_paths.append(path)

    def lemmas(self):
        return self._lemmas

    def lemma_names(self):
        return [lemma.name() for lemma in self._lemmas]

    def hypernyms(self):
        return [self._pwordnet.synset(hypernym) for hypernym in self._hypernyms]
        # return self._hypernyms

    def hypernym_paths(self):
        path_ = []
        for path in self._hypernym_paths:
            path_.append([self._pwordnet.synset(hypernym) for hypernym in path])
        return path_
        # return self._hypernym_paths

    def min_depth(self):
        pass

    def hyponyms(self):
        return [self._pwordnet.synset(hyponym) for hyponym in self._hyponyms]
        # return self._hyponyms

    def pos(self):
        return self._pos


class PLexicalUnit(wnsource.RLLexicalUnit):
    """PWN RL Source Lexical Unit.

    Parameters
    ----------
    synset : str
        Synset identifier
    lemma : str
        Lemma of Lexical Unit
    pos : int or str
        Lexical Unit pos
    """
    def __init__(self, synset, lemma, pos):
        self._synset = synset
        self._lemma = lemma
        self._pos = pos

    def id_(self):
        return '{}.{}'.format(self._synset, self._lemma)

    def name(self):
        return self._lemma

    def pos(self):
        return self._pos
