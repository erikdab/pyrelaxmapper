# -*- coding: utf-8 -*-
import logging

import numpy as np
# from nltk.corpus import wordnet as wn

# from pyrelaxmapper import conf
# from pyrelaxmapper.plwordnet.plsource import PLWordNet
# from pyrelaxmapper.plwordnet import queries
# from pyrelaxmapper.pwn.psource import PWordNet
# from pyrelaxmapper.wnmap import wnutils, wndict
from pyrelaxmapper.wnmap.stats import Statistics, Mapping

logger = logging.getLogger()


# Don't even know how useful this is!
def _initial_weights(target_synsets, translations):
    """Set initial weights based on the number of translations in every synset."""
    weights = np.zeros(len(target_synsets))

    # TODO: Consider if we can filter out more? Or add more weights somehow
    # Weights: sum of occurences of translations in synset
    for i, synset in enumerate(target_synsets):
        weights[i] += sum(1 for t in translations
                          if t in synset.lemma_names() or t in synset.name())

    candidates = len(weights.nonzero()[0])
    return weights, candidates


# Extremely slow!
def targets(target, translations):
    pass
    # target_synsets = []
    # for synset in target.synsets_all():
    #     lemmas = [lemma.lower() for lemma in synset.lemma_names()] + [synset.name()]
    #     if any([trans in lemmas for trans in translations]):
    #         target_synsets.append(synset)
    # return target_synsets


def mono(stats):
    """

    Parameters
    ----------
    stats : pyrelaxmapper.wnmapper.stats.Statistics

    Returns
    -------

    """
    logger.info('Starting monosemous mappings.')
    for synset in stats.to_map:
        if synset.id_() in stats.iteration().mappings:
            continue
        translations = stats.dictionary.translate(lemma for lemma in synset.lemma_names())

        targets = {}
        for trans in translations:
            targets.update({syn.name(): syn for syn in stats.wntarget.synsets(trans)})
        targets = list(targets.values())

        # weights = np.array([[1]])
        candidates = len(targets)

        # Add weights for upper/lower case differences, word order differences, morphy
        # etc., occurences
        # Not really helping now.
        # if candidates > 1:
        #     weights, candidates = _initial_weights(target_synsets, translations)

        if candidates == 0:
            stats.iteration().no_candidates.add(synset.id_())
        elif candidates == 1:
            # method = 'counts' if len(target_synsets) > candidates else 'monosemous'
            # target_synset = target_synsets[weights.nonzero()[0][0]]
            method = 'monosemous'
            target_synset = targets[0]

            mapping = Mapping(synset.id_(), target_synset, method)
            stats.one_translation[synset.id_()] = mapping
        else:
            stats.iteration().remaining[synset.id_()] = targets
    return stats
