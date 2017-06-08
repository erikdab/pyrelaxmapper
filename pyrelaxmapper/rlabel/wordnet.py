# -*- coding: utf-8 -*-
"""WordNet Base interface."""


class RLWordNet:
    """WordNet Interface.

    Define which features it supports. Maybe specify WordNet config"""
    def open(self):
        """Initializes access to WordNet data."""
        pass

    def close(self):
        """Cleans up after use."""
        pass

    def version(self):
        pass

    def synset(self, id_):
        """Find synset with id."""
        pass

    def synsets(self, lemma, pos=None):
        """Return all synsets including given lemma and part of speech."""
        pass

    def hypernyms(self, id_):
        pass

    def hyponyms(self, id_):
        pass

    def synsets_all(self):
        pass

    def mappings(self):
        """Existing mappings"""
        pass

    def pos(self):
        """All POS."""
        pass

    def domains(self):
        """All domains."""
        pass


class Synsets:
    """Interface holding synsets."""

    def search(self, name):
        pass

    def hyper(self):
        pass

    def hypo(self):
        pass

    def antonym(self):
        pass

    def holonym(self):
        pass

    def holo_mero(self):
        pass

    def similar(self):
        pass

    def pos(self):
        pass

    def pos_str(self):
        pass

    def domain(self):
        pass


class RLSynset:
    def id_(self):
        pass

    def lemmas(self):
        pass

    def lemma_names(self):
        pass

    def definition(self):
        pass

    def hypernyms(self):
        pass

    def hyponyms(self):
        pass

    def examples(self):
        pass

    def min_depth(self):
        pass


class RLLexicalUnit:
    """Relaxtion labeling Lexical Unit interface."""
    def id_(self):
        """Identifier."""
        pass

    def lemma(self):
        """Lemma."""
        pass

    def pos(self):
        """Part of speech."""
        pass


class Words:
    """Stores WordNet Words."""
    def gloss(self):
        pass

    def definition(self):
        pass

    def sensekeys(self):
        pass

    def matches(self, words):
        pass

    # TODO: What are empties?
    def remove_empties(self):
        pass

    def load_empties(self):
        pass

    def pos(self):
        pass

    def pos_str(self):
        pass

    def domain(self):
        pass


class Dictionary:
    pass
