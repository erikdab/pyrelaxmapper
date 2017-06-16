# -*- coding: utf-8 -*-
"""WordNet Base interface."""


# Faster creating cache.
# Smaller cache size.
# Validation of all mappings.
# If DB, relationships between all objects.
# TODO: Links between RLSynset and RLLexicalUnit and back
# (expect for plWordNet source)


class RLWordNet:
    """WordNet Interface.

    Define which features it supports. Maybe specify WordNet config"""
    def __repr__(self):
        format = "{}({})" if isinstance(self.version(), int) else "{}('{}')"
        return format.format(type(self).__name__, self.version())

    @staticmethod
    def name():
        """RL Source name.

        Returns
        -------
        str
        """
        pass

    @staticmethod
    def name_short():
        """RL Source short name.

        Returns
        -------
        str
        """
        pass

    def lang(self):
        """RL Source language.

        Returns
        -------
        str
        """
        pass

    def version(self):
        """RL Source version (any format).

        Returns
        -------
        str
        """
        pass

    def synset(self, id_):
        """Synset with id.

        Parameters
        ----------
        id_ : str or int
        """
        pass

    def synsets(self, lemma, pos=None):
        """All synsets containing lemma of desired POS.

        Parameters
        ----------
        lemma : str
            Lemma to search for.
        pos : str, optional
            POS to search for.
        """
        pass

    def synsets_all(self):
        """All synsets.

        Returns
        -------
        synsets: list of pyrelaxmapper.wnmap.wnsource.RLSynset
        """
        pass

    def all_hypernyms(self):
        pass

    def all_hyponyms(self):
        pass

    def mappings(self, target_wn):
        """Existing mappings

        Parameters
        ----------
        target_wn : str
            Name of target WordNet to look for existing mappings to.
        """
        pass

    def pos(self):
        """All POS.

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

    def empties(self):
        pass


class RLSynset:
    """RL Source Synset interface."""
    def __repr__(self):
        format = "{}({})" if isinstance(self.name(), int) else "{}('{}')"
        return format.format(type(self).__name__, self.name())

    def id_(self):
        """Unique identifier.

        Returns
        -------
        id_ : int or str or tuple
        """
        pass

    @staticmethod
    def name():
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
        lemmas : list of RLLexicalUnit
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

        Returns
        -------
        hypernyms : list of RLSynset
        """
        pass

    def hypernym_paths(self):
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
        pass

    def hyponyms(self):
        """Hyponyms.

        Returns
        -------
        hyponyms : list of RLSynset
        """
        pass

    # TODO: Need to standard on int/str/etc.
    def pos(self):
        """Part of speech.

        Returns
        -------
        pos : int or str
        """
        pass


class RLLexicalUnit:
    """RL Source Lexical Unit interface."""
    def __repr__(self):
        # tup = type(self).__name__, self._synset._name, self._name
        # return "{}('{}.{}')".format(*tup)
        format = "{}({})" if isinstance(self.name(), int) else "{}('{}')"
        return format.format(type(self).__name__, self.name())

    def id_(self):
        """Unique identifier."""
        pass

    def name(self):
        """Name, lemma.

        Returns
        -------
        str
        """
        pass

    def pos(self):
        """Part of speech.

        Returns
        -------
        pos : int or str
        """
        pass
