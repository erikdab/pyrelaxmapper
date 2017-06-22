# -*- coding: utf-8 -*-
"""Dictionary and translation utilities."""
import logging

logger = logging.getLogger()


class Dictionary:
    """Lemma to lemmas translation dictionary.

    Unlike the name suggestions, it can also search for candidates
    in a single language.
    """
    def translate(self, lemmas, cleaner, from_lang='', to_lang=''):
        """Search for translations for a lemma from language to target language.

        Parameters
        ----------
        lemmas : str
        cleaner : func
            Functions which cleans lemmas
        from_lang : str, optional
            Source language. If not specified, default is selected
        to_lang : str
            Target language. If not specified, default is selected

        Returns
        -------
        tuple
            (translated, not_translated)
            translated: a dict (key=source lemma, value: candidates)
            not_translated: a list of source lemmas without candidates
        """
        pass


class Translater(Dictionary):
    """Lemma to lemmas dictionary aggregator.

    Unlike the name suggestions, it can also search for candidates
    in a single language.

    Parameters
    ----------
    dictionaries : list of Dictionary
    """
    def __init__(self, dictionaries=None):
        if not dictionaries:
            dictionaries = []
        self._dicts = dictionaries
        self.dicts_size = [dict_.size() for dict_ in self._dicts]
        self.dicts_count = [0] * len(self._dicts)

    def translate(self, lemmas, cleaner, from_lang='', to_lang=''):
        if not isinstance(lemmas, list):
            lemmas = [lemmas]

        # Monolingual
        if not self._dicts:
            return [cleaner(lemma) for lemma in lemmas]

        translated = {}
        not_translated = set()

        for lemma in lemmas:
            lemma = cleaner(lemma)
            if lemma in translated or lemma in not_translated:
                continue
            for idx, dict_ in enumerate(self._dicts):
                dict_trans = dict_.translate(lemma, cleaner, from_lang, to_lang)
                if dict_trans:
                    translated.setdefault(lemma, set()).update(dict_trans)
                    self.dicts_count[idx] += 1
            if lemma not in translated:
                not_translated.add(lemma)

        translated = {key: list(values) for key, values in translated.items()}

        return translated, not_translated


def find_candidates(source_wn, target_wn, translater=None, cleaner=lambda x: x):
    """Search for candidates between wordnet synsets.

    Parameters
    ----------
    source_wn : pyrelaxmapper.wnmap.wnsource.WordNet
    target_wn : pyrelaxmapper.wnmap.wnsource.WordNet
    translater : Translater, optional
    cleaner : func
        Functions which cleans lemmas
    """
    candidates_dict = {}
    source_lemmas = source_wn.lemma_synsets(cleaner)
    target_lemmas = target_wn.lemma_synsets(cleaner)
    for source_lemma, source_synsets in source_lemmas.items():
        translations = translater.translate(source_lemma, cleaner,
                                            source_wn.lang(), target_wn.lang())
        candidates = [synset
                      for lemma in translations if lemma in target_lemmas
                      for synset in target_lemmas[lemma]]
        if not candidates:
            continue
        for synset in source_synsets:
            candidates_dict.setdefault(synset, set()).update(candidates)
    return {key: list(value) for key, value in candidates_dict.items()}
