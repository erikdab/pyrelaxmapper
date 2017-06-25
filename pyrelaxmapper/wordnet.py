# -*- coding: utf-8 -*-
"""WordNet interface."""
from enum import Enum


class POS(Enum):
    """Parts of speech."""
    NOUN = 'n'
    VERB = 'v'
    ADV = 'a'
    ADJ = 'r'
    UNSET = '_'


class WordNet:
    """WordNet Interface.

    Aims to provide a unified interface for accessing WordNet
    information to simplify writing code for multiple WordNets.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Config Parser with plWordNet config.
    section : str, optional
        Section inside parser which contains plWordNet config.
    """
    def __init__(self, parser, section, preload=True):
        if preload:
            self.load()

    def __repr__(self):
        return "{}({})".format(type(self).__name__, repr(self.version()))

    @staticmethod
    def name_full():
        """WordNet full name.

        Returns
        -------
        str
        """
        pass

    @staticmethod
    def name():
        """WordNet short name.

        Returns
        -------
        str
        """
        pass

    @staticmethod
    def uid():
        """WordNet type used for identification.

        Returns
        -------
        str
        """
        pass

    def __hash__(self):
        return hash((self.uid(), self.lang(), self.version()))

    def lang(self):
        """WordNet core language.

        Returns
        -------
        str
        """
        pass

    def version(self):
        """WordNet version.

        Returns
        -------
        version: str or int
        """
        pass

    def synset(self, uid):
        """Synset with id.

        Parameters
        ----------
        uid : str or int

        Returns
        -------
        Synset
        """
        pass

    def synsets(self, lemma, pos=None):
        """Synsets containing lemma of desired POS.

        Parameters
        ----------
        lemma : str
            Lemma to search for.
        pos : str, optional
            POS to search for, if not specified, any POS.

        Returns
        -------
        synsets : list of Synset
        """
        pass

    def all_synsets(self):
        """All synsets.

        Returns
        -------
        synset: list of Synset
        """
        pass

    def lemma_synsets(self, cleaner):
        """List of mappings from lemma to synset which contain it.

        Parameters
        ----------
        cleaner : func
        """
        lemmas = {}
        for synset in self.all_synsets():
            for lemma in synset.lemmas():
                lemmas.setdefault(cleaner(lemma.name()), []).append(synset.uid())
        return lemmas

    def mappings(self, other_wn, recurse=True):
        """Existing mappings with another wordnet.

        Parameters
        ----------
        other_wn : pyrelaxmapper.wordnet.WordNet
            Short name of target WordNet to look for existing mappings to.
        recurse : bool
            Whether to check the other wordnet, only once
        """
        if other_wn == self:
            return {synset.uid(): synset.uid() for synset in self.all_synsets()}
        elif recurse:
            return other_wn.mappings(self, False)
        return None

    # Could create unified enum
    def pos(self):
        """Parts of speech.

        Key is POS
        Value is the id as stored in the wordnet.

        Returns
        -------
        pos: dict
        """
        pass

    def domains(self):
        """All domains.

        Returns
        -------
        domains: list of str
        """
        pass

    def count_synsets(self):
        """Count of all synsets.

        Returns
        -------
        int
        """
        return 0

    def count_lunits(self):
        """Count of all lunits.

        Returns
        -------
        int
        """
        return 0

    def count_lemmas(self):
        """Count of all lemmas.

        Returns
        -------
        int
        """
        return 0

    def load(self):
        """Loads wordnet data and returns self."""
        return self

    def loaded(self):
        """Was wordnet loaded.

        Returns
        -------
        bool"""
        return True


class Synset:
    """WordNet Synset interface.

    Aims to provide a unified interface for accessing WordNet synset
    information to simplify writing code for multiple WordNets.
    """
    def __repr__(self):
        # Can list unitindex too!
        ellipsis_ = ',...' if self.count() > 1 else ''
        return "{}({})[{}{}]".format(type(self).__name__, self.uid(), self.name(), ellipsis_)

    def uid(self):
        """Synset unique identifier in wordnet dataset.

        Returns
        -------
        uid : int or str
        """
        pass

    def name(self):
        """Name. Default value: first lemma.

        Returns
        -------
        name : str
        """
        return next(self.lemmas()).name() if self.count() else ''

    def count(self):
        """Lemma count.

        Returns
        -------
        int
        """
        return 0

    def lemmas(self):
        """Lemmas.

        Returns
        -------
        lemmas : list of LexicalUnit
        """
        pass

    def lemma_names(self):
        """Lemma names.

        Returns
        -------
        lemma_names : list of str
        """
        pass

    @staticmethod
    def get_uids(synsets):
        if all(isinstance(el, list) for el in synsets):
            return [[synset.uid() for synset in group] for group in synsets]
        return [synset.uid() for synset in synsets]

    def hypernyms(self):
        """Hypernyms.

        Selects synsets which are hypernyms to this synset.

        Returns
        -------
        hypernyms : list of Synset
        """
        pass

    def hypernym_paths(self):
        """Hypernym paths.

        Selects synsets which are hypernyms to this synset.

        Returns
        -------
        hypernym_paths : list
        """
        pass

    def hypernym_layers(self, uids=False):
        """Hypernym paths.

        Returns
        -------
        hypernym_paths : list
        """
        pass

    def min_depth(self):
        """Minimum depth of hypernym_paths.

        Returns
        -------
        int
        """
        min_depth_ = None
        for path in self.hypernym_paths():
            if min_depth_ is None or min_depth_ < len(path):
                min_depth_ = len(path)
        return min_depth_

    def hyponyms(self):
        """Hyponyms.

        Returns
        -------
        hyponyms : list of Synset
        """
        pass

    def hyponym_layers(self, uids=False):
        """Hyponym layers.

        Returns
        -------
        hyponyms : list of Synset
        """
        pass

    def find_hyponym_layers(self):
        """

        Parameters
        ----------
        synset : pyrelaxmapper.wnmap.wnsource.Synset

        Returns
        -------
        list
        """
        todo = [self]
        hipo_layers = []
        while todo:
            do_next = []
            for node in todo:
                do_next.extend(node.hyponyms())
            todo = do_next
            if todo:
                hipo_layers.append(todo)
        return hipo_layers

    def antonyms(self):
        """Antonyms

        Returns
        -------
        antonyms : list of Synset
        """
        pass

    def pos(self):
        """Part of speech.

        Returns
        -------
        pos : POS
        """
        pass


class LexicalUnit:
    """WordNet Lemma interface.

    Aims to provide a unified interface for accessing WordNet lemma
    information to simplify writing code for multiple WordNets.
    """
    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.name())

    def uid(self):
        """Lemma unique identifier in database / corpus.

        Returns
        -------
        uid : int or str
        """
        pass

    def name(self):
        """Name.

        Returns
        -------
        str
        """
        pass

    def pos(self):
        """Part of speech.

        Returns
        -------
        pos : POS
        """
        pass
