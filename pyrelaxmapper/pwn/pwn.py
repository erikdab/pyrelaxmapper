# -*- coding: utf-8 -*-
import logging
import os

import nltk
from nltk.corpus import wordnet as wn

from pyrelaxmapper import wordnet

logger = logging.getLogger()


class PWordNet(wordnet.WordNet):
    """Princeton WordNet interface for the NTLK PWN corpus.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Config Parser with plWordNet config.
    section : str, optional
        Section inside parser which contains PWN config.
        Default selects the [source] section.
    """

    def __init__(self, parser, section, preload=True):
        self._config = self.Config(parser, section)
        self._version = ''

        self._synsets = {}
        self._hyponym_layers_uid = {}
        self._hypernym_layers_uid = {}
        self._pos = {}

        self._loaded = False
        super().__init__(parser, section, preload)

    # NLTK data dir?
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
            self.pos = parser.get('relaxer', 'pos', fallback='').split(',')
            self.dir = parser.get(section, 'nltk-data', fallback='')
            if self.dir and os.path.exists(self.dir):
                nltk.data.path.append(self.dir)

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
        return self._version

    def synset(self, uid):
        if isinstance(uid, str):
            return self._synsets_name.get(uid)
            # return next((syn for syn in self._synsets.values() if syn._name == uid), None)
        else:
            return self._synsets.get(uid)

    def synsets(self, lemma, pos=None):
        return [PSynset(self, synset) for synset in wn.synsets(lemma, pos)]

    def all_synsets(self):
        return self._synsets.values()

    def load(self):
        """Load PWN data from NLTK."""
        if not self._version:
            self._version = wn.get_version()

        text = repr(self)
        if not self._synsets:
            logger.info('{} Loading synsets, relations, lemmas, and other info.'.format(text))
            if self._config.pos:
                self._config.pos = self._config.pos[0]
            # offset() index and container
            self._synsets = {synset.offset(): PSynset(self, synset)
                             for synset in wn.all_synsets(self._config.pos)}
            # name() index
            self._synsets_name = {synset.name(): synset for synset in self._synsets.values()}

            logger.info('{} Calculating hyper/hypo layers.'.format(text))
            self._hypernym_layers_uid, self._hyponym_layers_uid = self.find_hh_layers()

            # for synset in self._synsets.values():
            #     synset.update_rels()

        if not self._pos:
            self._pos = {'n': wn.NOUN, 'v': wn.VERB, 'r': wn.ADV, 'a': wn.ADJ}

        self._loaded = True
        return self


class PSynset(wordnet.Synset):
    """Princeton WordNet synset interface for the NTLK PWN corpus.

    Parameters
    ----------
    pwordnet : PWordNet
    nltk_synset : nltk.corpus.reader.wordnet.Synset
        Synset
    """

    def __init__(self, pwordnet, nltk_synset):
        self._pwordnet = pwordnet
        self._uid = nltk_synset.offset()
        self._name = nltk_synset.name()
        # self._pos = nltk_synset.pos()
        # nltk.lexname() 'noun.animal'!!
        self._lemmas = []
        for lemma in nltk_synset.lemmas():
            self._lemmas.append(PLexicalUnit(lemma, self, lemma.name()))
        self._hypernyms = [syn.offset() for syn in nltk_synset.hypernyms()]
        self._hypernym_paths = []
        for path in nltk_synset.hypernym_paths():
            self._hypernym_paths.append([syn.offset() for syn in path])
        self._hyponyms = [syn.offset() for syn in nltk_synset.hyponyms()]
        self._hyponym_layers = []
        self._hypernym_layers = []
        self._hyponym_layers = None
        self._hypernym_layers = None
        # self._antonyms = [antonym for lemma in self._lemmas
        #                   for antonym in lemma.antonyms()]
        # Content style only required on target side?
        # gloss: nltk_synset.definition()
        # examples: nltk_synset.examples()

    def uid(self):
        return self._uid

    def name(self):
        return self._name

        # def update_rels(self):
        #     """Update relation links (reference)."""
        # text = repr(self._pwordnet)
        # logger.info('{} Loading hyponym layers.'.format(text))
        # self._hyponym_layers = self.find_hyponym_layers()
        # # logger.info('{} Loading hypernym_layers.'.format(text))
        # self._hypernym_layers = self.find_hypernym_layers()
        # # logger.info('{} Calculating hyponym_layers_uid.'.format(text))
        # self._hyponym_layers_uid = self.get_uids(self._hyponym_layers)
        # # logger.info('{} Calculating hypernym_layers_uid.'.format(text))
        # self._hypernym_layers_uid = self.get_uids(self._hypernym_layers)

    def lemmas(self):
        return self._lemmas

    def lemma_names(self):
        return (lemma.name() for lemma in self._lemmas)

    def hypernyms(self):
        return [self._pwordnet.synset(hypernym) for hypernym in self._hypernyms]

    def hypernym_paths(self):
        path_ = []
        for path in self._hypernym_paths:
            path_.append([self._pwordnet.synset(hypernym) for hypernym in path])
        return path_

    def hypernym_layers(self):
        if self._hypernym_layers is None:
            self._hypernym_layers = self._pwordnet._hypernym_layers_uid[self._uid]
        return self._hypernym_layers

    def hyponyms(self):
        return [self._pwordnet.synset(hyponym) for hyponym in self._hyponyms]

    def hyponym_layers(self):
        if self._hyponym_layers is None:
            self._hyponym_layers = self._pwordnet._hyponym_layers_uid[self._uid]
        return self._hyponym_layers

    def antonyms(self):
        return self._antonyms

    def pos(self):
        return self._pos


class PLexicalUnit(wordnet.LexicalUnit):
    """Princeton Wordnet lemma for the NLTK PWN corpus.

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
        self._uid = '{}.{}'.format(synset.name(), lemma)
        self._lemma = lemma
        self._antonyms = [antonym.name() for antonym in nltk_lemma.antonyms()]

    def synset(self):
        return self._synset

    def uid(self):
        return self._uid

    def name(self):
        return self._lemma

    def antonyms(self):
        return self._antonyms

    def pos(self):
        return self._synset.pos()
