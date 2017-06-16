# -*- coding: utf-8 -*-
"""Dict building utilities."""
import logging
import os
from xml.etree.ElementTree import ElementTree

import conf
from plwordnet import queries
from plwordnet.plsource import PLLexicalUnit
from pyrelaxmapper.wnmap import wnutils
from nltk.corpus import wordnet as wn

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

    def size(self):
        return len(self.dict_)

    @staticmethod
    def clean_trans(terms):
        terms_ = [wnutils.clean(term) for term in terms]
        filtered = list(filter(None, terms_))
        if not terms_[0] or len(filtered) < 2:
            return ['', '']
        morphy = [wn.morphy(term, wn.NOUN) for term in filtered[1:]]
        filtered += [morph for morph in morphy if morph not in filtered and morph]
        return filtered

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
    """Cascading Dict Dictionary
    Parameters
    ----------
    directory : string
        Directory containing dictionaries to cascade together.

        Structure:
          index.txt     # Dictionaries names (dir names) to load
          */dict.txt    # Translations for each dictionary

        'index.txt'   format: comma-separated ordered list, example:
            "dicts_dir1,dicts_dir3,dicts_dir2"
        'dict.txt'    format: tab-delimited translations, example:
            "term1\ttranslation1
             term2\ttranslation2"
    """

    def __init__(self, directory):
        super().__init__()
        self.name_ = 'Cascading Dicts'
        self.load(directory)

    def load(self, directory):
        filename = os.path.join(directory, 'index.txt')
        if not os.path.exists(filename):
            logger.error('index.txt is missing in path: {0}. '.format(directory))
            return
        with open(filename, 'r') as file:
            names = file.read().strip().split(',')
            index = [os.path.join(directory, name, 'dict.txt') for name in names]
        if not index:
            return
        for line in conf.yield_lines(index):
            self.add_terms(line.split('\t'))


# Could use Morphy?
# Could cache ony translated/not_translated?
# Lower case looses information!
class Translater:
    """Searches for translations for source lexical unit.

    Parameters
    ----------
    dicts : list of Dictionary
    """
    def __init__(self):
        # self.dicts = dicts
        # Count how many translations were found using dict.
        self.dicts_size = [0]
        self.dicts_count = [0]
        self.translated = {}
        self.not_translated = set()

    # Could also just receive just lemmas
    def build(self, dicts, lemmas):
        """

        Parameters
        ----------
        lemmas : list of str

        Returns
        -------
        tuple
            Tuple containing translated and not translated lexical units.
        """
        self.dicts_size = [dict.size() for dict in dicts]
        self.dicts_count = [0] * len(dicts)
        for lemma in lemmas:
            lemma = wnutils.clean(lemma)
            if lemma in self.translated or lemma in self.not_translated:
                continue
            for dict_id, dict_ in enumerate(dicts):
                dict_trans = dict_.search(lemma)
                if dict_trans:
                    self.translated.setdefault(lemma, set()).update(dict_trans)
                    self.dicts_count[dict_id] += 1
            if lemma not in self.translated:
                self.not_translated.add(lemma)

        return self.translated, self.not_translated


# Should try to accumulate the dicts if possible. Don't create unneccessary burden.
# Just put the translation into one class and load it all inside main to all for specifying
# different dictionaries, etc.
def translate():
    """Translate Polish Lexical Units to English."""
    group = 'Dicts'
    # no spaces     spaces
    # 644361        654061
    cd = wnutils.cached('Cascading Dicts', CascadingDict, args=conf.data('dicts'), group=group)
    # cd2 = wnutils.cached('cascading_dict2', CascadingDict, args=conf.data('dicts'))
    # 597655        597654
    ps = wnutils.cached('Piotr Saloni', PiotrSaloni, args=conf.data('PL-ANG'), group=group)
    # ps2 = wnutils.cached('piotr_saloni2', PiotrSaloni, args=conf.data('PL-ANG'))
    trans = Translater()

    # ete = {}
    # for k, t, t2 in zip(cd.dict_.keys(), cd.dict_.values(), cd2.dict_.values()):
    #     if t != t2:
    #         ete[k] = '{} {}'.format(t, t2)
    # ete2 = {}
    # for k, t, t2 in zip(ps.dict_.keys(), ps.dict_.values(), ps2.dict_.values()):
    #     if t != t2:

    #         ete2[k] = '{} {}'.format(t, t2)
    lunits = {}
    for lunit in queries.lunits(conf.make_session(), [2]):
        lunits[lunit.lemma] = PLLexicalUnit(lunit.id_, lunit.lemma, lunit.pos)
    lemmas = [lunit.name() for lunit in lunits.values()]

    # Morphy: cd: 1439 ps: 1786
    # Old:
    # 73380, 252578
    # 39412, 213659
    # Improved:
    # 57423/127354
    # [54828, 54994]
    # Dicts:[44296, 55678] Total:57168 of 128213
    # Dicts:[55531, 55720] Total:58158 of 128213
    # Clearly we DON'T WANT TO clean, because we lose data \/. Use it as test though.
    # NEED TO USE UNIFORM! Clean same way everywhere.
    # Dicts:[54848, 55013] Total:57443 of 127310
    # Could measure how much each one gave us..
    trans.build([cd, ps], lemmas)
    total = len(trans.translated) + len(trans.not_translated)
    logger.info('Dicts:{} Total:{} of {}'.format(trans.dicts_count, len(trans.translated), total))
    return trans
