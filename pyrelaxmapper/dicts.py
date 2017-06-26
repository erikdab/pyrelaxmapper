# -*- coding: utf-8 -*-
"""Dictionary and translation utilities."""
import logging

logger = logging.getLogger()


# TODO: Validate multiple dicts!
class Translater:
    """Lemma to lemmas dictionary aggregator.

    Unlike the name suggestions, it can also search for candidates
    in a single language.

    Parameters
    ----------
    cleaner : func
    parser : configparser.ConfigParser
    section : str
    preload : bool
    """
    def __init__(self, dictionaries, cleaner):
        self._dicts = dictionaries
        self.cleaner = cleaner

    def translate(self, lemmas):
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
        if not isinstance(lemmas, list):
            lemmas = [lemmas]

        cleaner = self.cleaner
        # Monolingual
        if not self._dicts:
            return [cleaner(lemma) for lemma in lemmas]

        translated = {}
        not_translated = set()

        for lemma in lemmas:
            lemma = cleaner(lemma)
            if lemma in translated or lemma in not_translated:
                continue
            # for idx, _dict in enumerate(self._dicts):
            dict_trans = self._dicts.get(lemma, None)
            if dict_trans:
                translated.setdefault(lemma, set()).update(dict_trans)
            if lemma not in translated:
                not_translated.add(lemma)

        translated = {key: list(values) for key, values in translated.items()}

        return translated, not_translated

    def count(self):
        """Number of translations.

        Returns
        -------
        int
        """
        return sum(len(dict_) for dict_ in self._dicts)


def find_candidates(source_lemmas, target_lemmas, translater):
    """Search for candidates between wordnet synsets.

    Parameters
    ----------
    source_wn : dict
    target_wn : dict
    cleaner : func
        Functions which cleans lemmas
    translater : Translater, optional
    """
    candidates_dict = {}
    for source_lemma, source_synsets in source_lemmas.items():
        translations, _ = translater.translate(source_lemma)
        candidates = [synset
                      for lemma in translations if lemma in target_lemmas
                      for synset in target_lemmas[lemma]]
        if not candidates:
            continue
        for synset in source_synsets:
            candidates_dict.setdefault(synset, set()).update(candidates)
    return {key: list(value) for key, value in candidates_dict.items()}
