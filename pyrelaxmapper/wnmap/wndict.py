# -*- coding: utf-8 -*-
"""Dict building utilities."""
import logging
import os
from xml.etree.ElementTree import ElementTree

import conf
from plwordnet import queries
from plwordnet.plsource import PLLexicalUnit
from pyrelaxmapper import utils
from wnmap import wnutils

logger = logging.getLogger()


# Should keep symbols.
class Dictionary:
    """Dictionary translation source."""
    def __init__(self):
        self.dict_ = {}
        self.name_ = ''

    def search(self, lemma):
        """Search in Dictionary for translations."""
        return self.dict_[lemma] if lemma in self.dict_ else []

    def name(self):
        return self.name_

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self.name())

    @staticmethod
    def clean_trans(terms):
        terms_ = [wnutils.clean(term) for term in terms]
        filtered = list(filter(None, terms_))
        return filtered if terms_[0] and len(filtered) >= 2 else ['', '']

    def add_terms(self, terms):
        terms_ = self.clean_trans(terms)
        self.dict_.setdefault(terms_[0], set()).update(terms_[1:])


class PiotrSaloni(Dictionary):
    def __init__(self, directory):
        super().__init__()
        self.name_ = 'Piotr Saloni'
        self.load(directory)

    def load(self, directory):
        files = ['A-J.txt', 'K-P.txt', 'R-Z.txt']
        for file in files:
            tree = ElementTree().parse(os.path.join(directory, file))
            for element in tree:
                self.add_terms([node.text for node in element])


class CascadingDict(Dictionary):
    def __init__(self, directory):
        super().__init__()
        self.name_ = 'Cascading Dicts'
        self.load(directory)

    def load(self, directory):
        __, index = conf.load_dicts(directory)
        if not index:
            return
        i = 0
        for line in conf.yield_lines(index):
            self.add_terms(line.split('\t'))


class Translater:
    """Searches for translations for source lexical unit.

    Parameters
    ----------
    dicts : list of Dictionary
    """
    def __init__(self, dicts):
        self.dicts = dicts
        # Count how many translations were found using dict.
        self.dicts_count = [0] * len(dicts)
        self.translated = {}
        self.not_translated = set()

    # Could also just receive just lemmas
    def translate(self, lemmas):
        """

        Parameters
        ----------
        lemmas : list of str

        Returns
        -------
        tuple
            Tuple containing translated and not translated lexical units.
        """
        for lemma in lemmas:
            if lemma in self.translated or lemma in self.not_translated:
                continue
            cleaned = wnutils.clean(lemma)
            for dict_id, dict_ in enumerate(self.dicts):
                dict_trans = dict_.search(cleaned)
                if dict_trans:
                    self.translated.setdefault(lemma, set()).update(dict_trans)
                    self.dicts_count[dict_id] += 1
            if lemma not in self.translated:
                self.not_translated.add(lemma)

        return self.translated, self.not_translated


def translate():
    """Translate Polish Lexical Units to English."""
    # no spaces     spaces
    # 644361        654061
    cd = wnutils.cached('cascading_dict', CascadingDict, args=conf.data('dicts'))
    # 597655        597654
    ps = wnutils.cached('piotr_saloni', PiotrSaloni, args=conf.data('PL-ANG'))
    trans = Translater([cd, ps])

    lunits = {}
    for lunit in queries.lunits(conf.make_session(), [2]):
        lunits[lunit.lemma] = PLLexicalUnit(lunit.id_, lunit.lemma, lunit.pos)
    lemmas = [lunit.name() for lunit in lunits.values()]

    # Old:
    # 73380, 252578
    # 39412, 213659
    # Improved:
    # 57423/127354
    # [54828, 54994]
    # Dicts:[44296, 55678] Total:57168 of 128213
    # Could measure how much each one gave us..
    trans.translate(lemmas)
    total = len(trans.translated) + len(trans.not_translated)
    logger.info('Dicts:{} Total:{} of {}'.format(trans.dicts_count, len(trans.translated), total))
    return trans.translated
