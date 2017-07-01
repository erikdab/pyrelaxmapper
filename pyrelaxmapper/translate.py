# -*- coding: utf-8 -*-
"""Dictionary and translation utilities."""
import logging
from collections import defaultdict

logger = logging.getLogger()


class Dictionary:
    # Maybe also source_wn, target_wn (so that we can analyze POS)
    def translate(source_lemmas, target_lemmas):
        pass


def find_candidates(source_lemmas, target_lemmas, dictionary, cleaner):
    """Search for candidates between wordnet synsets.

    Parameters
    ----------
    source_wn : dict
    target_wn : dict
    cleaner : func
        Functions which cleans lemmas
    translater : Translater, optional
    """
    if not dictionary:
        # candidates_dict = {source: source for source in source_lemmas.values()}
        return [], ((100, len(source_lemmas)), (100, len(target_lemmas)))
    candidates_dict = defaultdict(set)
    s_lemma_match = 0
    d_lemma_match = 0
    d_lemmas = set()
    for source_lemma, source_synsets in source_lemmas.items():
        translations = dictionary.get(source_lemma, None)
        if not translations:
            continue
        s_lemma_match += 1
        candidates = {synset
                      for lemma in translations
                      for synset in target_lemmas.get(lemma, [])}
        if not candidates:
            continue
        d_lemmas.update(candidates)
        for synset in source_synsets:
            candidates_dict[synset].update(candidates)
    d_lemma_match = len(d_lemmas)
    return candidates_dict, ((s_lemma_match, len(source_lemmas)),
                             (d_lemma_match, len(target_lemmas)))
    # return {key: list(value) for key, value in candidates_dict.items()}
