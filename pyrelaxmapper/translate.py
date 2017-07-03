# -*- coding: utf-8 -*-
"""Dictionary and translation utilities."""
import logging
from collections import defaultdict
import re

logger = logging.getLogger()


class Translater:
    """Translates synsets between wordnets using dictionaries."""
    def __init__(self, cleaner, dictionaries):
        self.cleaner = cleaner
        self.dicts = dictionaries

        self.s_trans = 0
        self.d_lemma_match = 0
        self.d_syn_match = 0

        self.no_alpha = 0
        self.has_digits = 0
        self.multi = 0
        self.has_dash = 0

        self.candidates = {}

    def translate(self, o_lemma_synsets, d_lemma_synsets):
        """Search for candidates between wordnet synsets."""
        if not self.dicts:
            candidates_mono = defaultdict(set)
            for source_lemma, source_synsets in o_lemma_synsets.items():
                translations = d_lemma_synsets.get(source_lemma, set())
                for source_synset in source_synsets:
                    candidates_mono[source_synset].extend(d_lemma_synsets.get(trans)
                                                          for trans in translations)

            self.candidates = candidates_mono
            return self

        log_title = type(self).__name__

        self.no_alpha = sum(1 for key in self.dicts.keys() if not re.search('[a-zA-Z]', key))
        self.has_digits = sum(1 for key in self.dicts.keys() if not re.search('[a-zA-Z]', key))
        self.multi = sum(1 for key in self.dicts.keys() if '_' in key)
        self.has_dash = sum(1 for key in self.dicts.keys() if '-' in key)

        all_candidates = defaultdict(set)
        d_uniq_syn = set()

        logger.info('{} Translating.'.format(log_title))
        for source_lemma in o_lemma_synsets.keys():
            translations = self.dicts.get(source_lemma, set())
            if not translations:
                continue

            source_synsets = set(o_lemma_synsets.get(source_lemma, set()))
            self.s_trans += 1

            syn_candidates = {synset
                              for lemma in translations
                              for synset in d_lemma_synsets.get(lemma, [])}

            if not syn_candidates:
                continue

            self.d_lemma_match += len(syn_candidates)

            d_uniq_syn.update(syn_candidates)
            for synset in source_synsets:
                all_candidates[synset].update(syn_candidates)

        self.d_syn_match = len(d_uniq_syn)
        self.candidates = all_candidates
        return self
