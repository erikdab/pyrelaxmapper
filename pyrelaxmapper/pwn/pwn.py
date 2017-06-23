# -*- coding: utf-8 -*-
from nltk.corpus import wordnet as wn

from pyrelaxmapper import wordnet


class PWordNet(wordnet.WordNet):
    """WordNet WordNet interface for the NTLK version of PWN.

    Parameters
    ----------
    parser " configparser.ConfigParser
        Config Parser with plWordNet config.
    section : str, optional
        Section inside parser which contains PWN config.
        Default selects the [source] section.
    """
    def __init__(self, parser, section='source'):
        self._config = self.Config(parser, section)
        self._version = ''

        self._synsets = None

        self._load_data()

    class Config:
        """PWN WordNet configuration.

        Parameters
        ----------
        parser : configparser.ConfigParser
        section : str, optional
            Section inside parser which contains PWN config.
            Default selects the [source] section.
        """
        def __init__(self, parser, section='source'):
            self.db_file = parser[section]['db-file']
            self.pos = parser['relaxer']['pos']

    POS = {'v': 1, 'n': 2, 'r': 3, 'a': 4}

    @staticmethod
    def name_full():
        return 'WordNet'

    @staticmethod
    def name():
        return 'PWN'

    @staticmethod
    def uid():
        return 'pwn-nltk'

    def lang(self):
        return 'en-us'

    def version(self):
        return '{} {}'.format(self.name(), self._version)

    def synset(self, id_):
        return self._synsets[id_]

    def synsets(self, lemma, pos='n'):
        return [PSynset(self, synset) for synset in wn.synsets(lemma, pos)]

    def all_synsets(self):
        return self._synsets.values()

    def all_hypernyms(self):
        return ((synset.offset(), synset.hypernyms()) for synset in self._synsets)

    def all_hyponyms(self):
        return ((synset.offset(), synset.hyponyms()) for synset in self._synsets)

    def _load_data(self):
        """Load PWN data from NLTK."""
        if not self._synsets:
            self._synsets = {synset.offset(): PSynset(self, synset)
                             for synset in wn.all_synsets(self._config.pos)}

            for synset in self._synsets.values():
                synset.update_rels()

        if not self._pos:
            self._pos = {'n': wn.NOUN, 'v': wn.VERB, 'r': wn.ADV, 'a': wn.ADJ}

        if not self._version:
            self._version = wn.get_version()


class PSynset(wordnet.Synset):
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
            self._lemmas.append(PLexicalUnit(lemma, self, lemma.name()))
        self._hypernyms = [syn.offset() for syn in nltk_synset.hypernyms()]
        self._hypernym_paths = []
        for path in nltk_synset.hypernym_paths():
            self._hypernym_paths.append([syn.offset() for syn in path])
        self._hyponyms = [syn.offset() for syn in nltk_synset.hyponyms()]
        self._antonyms = [antonym for lemma in self._lemmas
                          for antonym in lemma.antonyms()]

    def id_(self):
        return self._id

    def name(self):
        return self._name

    def update_rels(self):
        """Update relation links (reference)."""
        self._hyponym_layers = self.find_hyponym_layers()

    def lemmas(self):
        return self._lemmas

    def lemma_names(self):
        return [lemma.name() for lemma in self._lemmas]

    def hypernyms(self):
        return [self._pwordnet.synset(hypernym) for hypernym in self._hypernyms]

    def hypernym_paths(self):
        path_ = []
        for path in self._hypernym_paths:
            path_.append([self._pwordnet.synset(hypernym) for hypernym in path])
        return path_

    def hyponyms(self):
        return [self._pwordnet.synset(hyponym) for hyponym in self._hyponyms]

    def hyponym_layers(self):
        return self._hyponym_layers

    def antonyms(self):
        return self._antonyms

    def pos(self):
        return self._pos


class PLexicalUnit(wordnet.LexicalUnit):
    """PWN RL Source Lexical Unit.

    Parameters
    ----------
    nltk_lemma : nltk.corpus.reader.wordnet.Lemma
    synset : PSynset
        Synset identifier
    lemma : str
        Lemma of Lexical Unit
    pos : int or str
        Lexical Unit pos
    """
    def __init__(self, nltk_lemma, synset, lemma):
        self._synset = synset
        self._id = '{}.{}'.format(synset.name(), lemma)
        self._lemma = lemma
        self._antonyms = [antonym.name() for antonym in nltk_lemma.antonyms()]

    def synset(self):
        return self._synset

    def id_(self):
        return self._id

    def name(self):
        return self._lemma

    def antonyms(self):
        return self._antonyms

    def pos(self):
        return self._synset.pos()
