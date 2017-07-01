# -*- coding: utf-8 -*-
"""Dictionary and translation utilities."""
import logging
from collections import defaultdict
import re

logger = logging.getLogger()


class Dictionary:
    # Maybe also source_wn, target_wn (so that we can analyze POS)
    def translate(self, source_lemmas, target_lemmas, cleaner):
        pass

    def uid(self):
        """Dictionary unique name."""
        pass


# Sometimes words in terms can be reversed, etc.
# TODO: Receive dictionaries too I think
class Translater:
    def __init__(self, cleaner, dictionaries):
        self.cleaner = cleaner
        # Shouldn't be stored
        self.dicts = dictionaries

        # Stats
        # dict of namedtuples (dict key is WordNet hash)
        # self.s_any_match = 0
        # self.s_exact_match = 0
        # self.s_cleaned_match = 0
        # self.s_lemma_match = 0
        #
        # self.d_any_match = 0
        # self.d_exact_match = 0
        # self.d_cleaned_match = 0
        # self.d_lemma_match = 0

        self.s_trans = 0
        self.d_lemma_match = 0
        self.d_syn_match = 0

        # self.cleaned_match = 0
        # self.exact_match = 0

        # self.diff_same = 0
        # self.diff_lower = 0
        # self.diff_clean = 0
        self.no_alpha = 0
        self.has_digits = 0
        self.multi = 0
        self.has_dash = 0

        self.candidates = {}

    # source_lunit, target_lunit
    def translate(self, source_lemmas, target_lemmas):
        """Search for candidates between wordnet synsets."""
        if not self.dicts:
            # candidates_dict = {source: source for source in source_lemmas.values()}
            return [], ((100, len(source_lemmas)), (100, len(target_lemmas)))

        log_title = type(self).__name__

        # _load_permutations() Place in seperate function
        # source_lemmas_c = defaultdict(set)
        # source_lemmas_c2 = defaultdict(set)
        # target_lemmas_c = defaultdict(set)
        # target_lemmas_c2 = defaultdict(set)
        # dictionary_c = defaultdict(set)
        #
        # logger.info('{} Cleaning source lemmas.'.format(log_title))
        # for lemma, source_synsets in source_lemmas.items():
        #     source_lemmas_c[lemma].add(self.cleaner(lemma))
        #     source_lemmas_c2[self.cleaner(lemma)].update(source_synsets)
        # logger.info('{} Cleaning target lemmas.'.format(log_title))
        # for lemma, source_synsets in target_lemmas.items():
        #     target_lemmas_c[lemma].add(self.cleaner(lemma))
        #     target_lemmas_c2[self.cleaner(lemma)].update(source_synsets)
        #
        # # Could cache cleaned dict as well as morphy dict.
        # logger.info('{} Cleaning dictionaries.'.format(log_title))
        # for lemma, trans in self.dicts.items():
        #     dictionary_c[self.cleaner(lemma)].update(trans)

        # self.diff_same = len(self.dicts.keys() & dictionary_c.keys())
        # self.diff_lower =len(set(key.lower() for key in self.dicts.keys()) - dictionary_c.keys())
        # self.diff_clean = len(self.dicts.keys() - dictionary_c.keys())
        self.no_alpha = sum(1 for key in self.dicts.keys() if not re.search('[a-zA-Z]', key))
        self.has_digits = sum(1 for key in self.dicts.keys() if not re.search('[a-zA-Z]', key))
        self.multi = sum(1 for key in self.dicts.keys() if '_' in key)
        # TODO: Check this
        self.has_dash = sum(1 for key in self.dicts.keys() if '-' in key)
        # Piotr Saloni has POS

        # TODO: Improve naming
        # Morphy
        # for lemma, synsets in source_lemmas.items():
        #     source_lemmas_c[self.cleaner(lemma)].update(synsets)
        # for lemma, synsets in target_lemmas.items():
        #     target_lemmas_c[self.cleaner(lemma)].update(synsets)
        # for lemma, trans in self.dicts.items():
        #     dictionary_c[self.cleaner(lemma)].update([self.cleaner(tran) for tran in trans])

        candidates_dict = defaultdict(set)
        d_uniq_syn = set()
        logger.info('{} Translating.'.format(log_title))
        for source_lemma in source_lemmas.keys():
            # _find_translations() place in seperate function
            translations = self.dicts.get(source_lemma, set())
            source_synsets = set(source_lemmas.get(source_lemma, set()))
            # self.s_exact_match += 1
            # translations_c = set()
            # source_synsets_c = set()
            # if not translations:
            # for source_lemma_c in source_lemmas_c.get(source_lemma):
            #     source_synsets_c.update(source_lemmas_c2.get(source_lemma_c))
            #     translations_c.update(dictionary_c.get(source_lemma_c, set()))
            #     self.s_cleaned_match += 1
            # translations_m = dictionary_c.get(source_lemma, None)
            # if not translations:
            #     # translations_m = dictionary_c.get(source_lemma, None)
            #     translations = translations_m
            #     self.s_lemma_match += 1
            if not translations:  # and not translations_c:
                continue
            self.s_trans += 1
            #
            # candidates = {synset
            #               for lemma in translations
            #               for synset in target_lemmas.get(lemma, [])}
            candidates = {synset
                          for lemma in translations
                          for synset in target_lemmas.get(lemma, [])}
            # self.exact_match += len(candidates)
            # if not candidates:
            # candidates_c = {synset
            #                 for lemma in translations_c
            #                 for synset in target_lemmas_c2.get(lemma, [])}
            # candidates.update(candidates_c)

            if not candidates:
                continue
            self.d_lemma_match += len(candidates)
            d_uniq_syn.update(candidates)
            for synset in source_synsets:
                candidates_dict[synset].update(candidates)
        self.d_syn_match = len(d_uniq_syn)
        self.candidates = candidates_dict
        return self
