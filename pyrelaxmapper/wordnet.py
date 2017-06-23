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
    """
    def __repr__(self):
        info = "{}({})" if isinstance(self.version(), int) else "{}('{}')"
        return info.format(type(self).__name__, self.version())

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

    def mappings(self, other_wn):
        """Existing mappings with another wordnet.

        Parameters
        ----------
        other_wn : str
            Short name of target WordNet to look for existing mappings to.
        """
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


class Synset:
    """WordNet Synset interface.

    Aims to provide a unified interface for accessing WordNet synset
    information to simplify writing code for multiple WordNets.
    """
    def __repr__(self):
        info = "{}({})" if isinstance(self.name(), int) else "{}('{}')"
        return info.format(type(self).__name__, self.name())

    def uid(self):
        """Synset unique identifier in database / corpus.

        Returns
        -------
        uid : int or str
        """
        pass

    def name(self):
        """Name.

        Returns
        -------
        name : str
        """
        pass

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

    def hypernym_layers(self):
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

    def hyponym_layers(self):
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
        info = "{}({})" if isinstance(self.name(), int) else "{}('{}')"
        return info.format(type(self).__name__, self.name())

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

