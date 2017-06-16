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

    @staticmethod
    def name():
        return 'WordNet'

    @staticmethod
    def name_short():
        return 'PWN'

    def lang(self):
        return 'en-us'

    def version(self):
        return self._version

    def synset(self, id_):
        return self._synsets[id_]

    # Uses morphy, etc.
    def synsets(self, lemma, pos='n'):
        return [PSynset(self, synset) for synset in wn.synsets(lemma, pos)]

    def synsets_all(self):
        return self._synsets.values()

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
            self._synsets = {}
            # i = 0
            for synset in wn.all_synsets(pos):
                self._synsets[synset.offset()] = PSynset(self, synset)
                # if i > 0 and i % 300 == 0:
                #     break
                # i += 1

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
        self._id = nltk_synset.offset()
        self._name = nltk_synset.name()
        self._pos = nltk_synset.pos()
        # nltk.lexname() 'noun.animal'!!
        self._lemmas = []
        for lemma in nltk_synset.lemmas():
            self._lemmas.append(PLexicalUnit(self, lemma.name()))
        self._hypernyms = [syn.offset() for syn in nltk_synset.hypernyms()]
        self._hypernym_paths = []
        for path in nltk_synset.hypernym_paths():
            self._hypernym_paths.append([syn.offset() for syn in path])
        self._hyponyms = [syn.offset() for syn in nltk_synset.hyponyms()]
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
    synset : PSynset
        Synset identifier
    lemma : str
        Lemma of Lexical Unit
    pos : int or str
        Lexical Unit pos
    """
    def __init__(self, synset, lemma):
        self._synset = synset
        self._id = '{}.{}'.format(synset.name(), lemma)
        self._lemma = lemma

    def synset(self):
        return self._synset

    def id_(self):
        return self._id

    def name(self):
        return self._lemma

    def pos(self):
        return self._synset.pos()
