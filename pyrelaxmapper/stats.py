# -*- coding: utf-8 -*-
import logging

import numpy as np

logger = logging.getLogger()


class Stats:
    """Algorithm Statistical calculations and analytics.

    Parameters
    ----------
    status : pyrelaxmapper.status.Status
    """

    def __init__(self, status):
        self.status = status

    def stat_mapping(self):
        cand = list(self.status.candidates.values())
        counts = np.array([len(node.labels) for node in cand])
        n = 10
        counts_max = counts.argsort()[-n][::-1]
        no_translations = [synset.uid() for synset in self.status.source_wn.all_synsets()
                           if synset.uid() not in self.status.candidates]
        stats = {
            'n_nodes': len(self.status.candidates),
            'n_labels': sum(counts),
            'most_ambiguous': cand[counts_max],
            'labels_max': 0,
            'labels_min': 0,
            'labels_avg': 0,
            'n_connections_per_type': 0,
            'n_stable': 0,
            'n_completed': 0,
            'n_monosemous': 0,
            'n_polysemous': 0,
            'n_no_translations': no_translations,
        }
        return stats

    def stat_wn_coverage(self):
        """Statistics about coverage of the source vs target wordnet.

        Returns
        -------
        dict
        """
        manual = self.status.source_wn.mappings(self.status.target_wn)
        stats = {
            'all_synsets': self.status.source_wn.count_synsets(),
            'manual': len(manual),
            'candidates': len(self.status.candidates),
            'monosemous': len(self.status.monosemous),
            'polysemous': len(self.status.polysemous),
        }
        return stats

    def stat_translation(self, print_stats=True):
        avg = 0.0
        max_ = None
        min_ = None
        candidates = self.status.candidates
        for key, candidate in candidates.items():
            count = len(candidate)
            if max_ is None or count > max_:
                max_ = count
            if min_ is None or count < min_:
                min_ = count
            avg += count
        avg = avg / len(candidates)
        stats = {
            'translations': 'Translations, count: {}'
            .format(self.status.config.translater().count()),
            # Source wordnet coverage
            'candidates_avg': avg,
            'candidates_min': min_,
            'candidates_max': max_,
        }
        return stats

    def stat_loading(self):
        """Statistics about speed of starting up from cached vs not."""
        stats = {
            'cache': 0,
            'live': 0
        }
        return stats

    def stat_wordnets(self, print_stats=True):
        wordnets = {'source': self.status.source_wn}
        if self.status.source_wn != self.status.target_wn:
            wordnets['target'] = self.status.target_wn
        stats = {}
        for key, wordnet in wordnets.items():
            stats.update({
                key+'synsets': 'Translations, count: {}'.format(wordnet.count_synsets()),
                key+'lunits': 'Translations, count: {}'.format(wordnet.count_lunits())
                # Hiper/hypo relations
            })
            logger.info('Translations, count: {}'.format(len(wordnet)))
            logger.info(
                'Source synsets, count: {}'.format(len(self.status.source_wn.all_synsets())))
            logger.info(
                'Target synsets, count: {}'.format(len(self.status.target_wn.all_synsets())))
        return stats

    def stat_iterations(self, print_stats=True):
        stats = {}
        for iteration in self.status.iterations.values():
            stats.update({iteration.index(): self.stat_iteration(iteration, False)})
        return stats

    def stat_iteration(self, iteration=None, print_stats=True):
        """Statistics about an iteration of the relaxational labeling algorithm.

        Parameters
        ----------
        iteration : pyrelaxmapper.stats.Iteration
        print_stats : boolean

        Returns
        -------
        dict
        """
        if not iteration:
            iteration = self.status.iteration()
        stats_dict = {
            'monosemic': 'Found {} monosemic mappings in iteration {}'
            .format(len(iteration.mappings), iteration.index()),
            'changes': 'Decreased candidates on {} nodes in iteration {}'
            .format(len(iteration.remaining), iteration.index())
        }
        if print_stats:
            self.print_stats(stats_dict)
        return stats_dict

    def print_stats(self, stats_dict):
        print('\n'.join(stats_dict.values()))
