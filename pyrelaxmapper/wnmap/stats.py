# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger()


class Mapping:
    """RL Mapping class between a source and target unit.

    """

    # class Method(Enum):
    #     """Mapping condition used."""
    #     dict = auto()
    #     counts = auto()
    #     rlabel = auto()
    #     manual = auto()

    def __init__(self, source_id, target_id, method='', info=''):
        self.source_id = source_id
        self.target_id = target_id
        self.info = info
        self.method = method

    def __repr__(self):
        return '{}->{} ({})'.format(self.source_id, self.target_id, self.method)


class Iteration:
    """Status of Relaxation Labeling algorithm."""

    def __init__(self, statistics, remaining, iteration=0):
        self._statistics = statistics
        # Dict with source id as key
        # Could keep only remaining and then move to mappings at end of iteration.
        self.mappings = {}
        self.remaining = remaining

        # We have not found any target candidates (using translations)
        self.no_candidates = set()
        # We have not found source in translations.
        # self.no_translations = set()

        self._iteration = iteration + 1
        # self.iteration
        # self.iteration results.
        # I Could have Iteration Results! Only iterations which have changes are noted,
        # and only the changes are saved! mapped is checked in all iterations!

    def next_iteration(self):
        return Iteration(self._statistics, self.remaining, self._iteration)

    def iteration(self):
        return self._iteration

    def mapping_stats(self):
        # logger.info('remaining {}; no translations {}; translated: {}, using weights: {}'
        #             .format(remaining_c, not_translated, translated, using_weights))
        # logger.info('no_translations: {}, no_translations_lu: {}'
        #             .format(len(no_translations), len(no_translations_lu)))
        pass


class Statistics:
    """Status of Relaxation Labeling algorithm."""

    def __init__(self, relaxmapper):
        self.relaxmapper = relaxmapper
        # Links
        # self.wnsource = None
        # self.wntarget = None
        self.iterations = [Iteration(self, relaxmapper.polysemous())]
        # + Already mapped
        self.mappings = relaxmapper.monosemous()
        # self.dictionary = None
        # self.monosemous = None
        # self.polysemous = None
        # Only one translation found. Doesn't change with iterations.
        # self.one_translation = {}
        # Dict with source id as key
        # List of lemmas with no translation
        # List of synsets with no candidates
        # self.no_translations = set()
        # nNodes
        # nLabels
        # list of X most ambiguous nodes
        # maxLabelsPerNode
        # nConnections
        # nTrans = nMulTrans = nNoTrans
        # nRelax
        # nCompleted
        # nStable
        # nConnectionsPerType
        # Create CSV Report! or even XLSX! (or ODF)
        # CSV is built into Python, XLSX openpyxl,
        # Create graphs.

    def push_iteration(self):
        it = self.iteration()
        self.mappings.extend(it.mappings)
        next_it = Iteration(self, it.remaining, it.iteration())
        self.iterations.append(next_it)
        return self.iteration()

    def iteration(self):
        return self.iterations[-1]

    def mapping_info(self, candidates):
        avg = 0.0
        max = None
        min = None
        for key, candidate in candidates.items():
            count = len(candidate)
            if max is None or count > max:
                max = count
            if min is None or count < min:
                min = count
            avg += count
        avg = avg / len(candidates)
        # ALL:  avg:14.81, max:491, min:1
        # POLY: avg:20.74, max:491, min:2
        print('avg:{:.2f}, max:{}, min:{}'.format(avg, max, min))

    def coverage(self):
        pass
        # manual_count = sum(1 for synset in manual if synset.id_() in candidates)
        # manual_coverage = manual_count / len(manual)
        # full_len = len(source_wn.synsets_all())
        # full_coverage = len(candidates) / full_len
        # logger.info(
        # 'Manual coverage: {}/{}: {:.2f}%'.format(
        #     manual_count, len(manual), 100 * manual_coverage))
        # logger.info(
        #     'Full coverage: {}/{}: {:.2f}%'.format(
        # len(candidates), full_len, 100 * full_coverage))

    def wordnet_info(self):
        pass
        # logger.info('Translations, count: {}'.format(len(self.dictionary)))
        # logger.info('Source synsets, count: {}'.format(len(self.wnsource.all_synsets())))
        # logger.info('Target synsets, count: {}'.format(len(self.wntarget.all_synsets())))
