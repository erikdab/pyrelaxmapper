# -*- coding: utf-8 -*-
import csv
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

    def stat_iteration(self, iteration=None, full=False):
        if not iteration:
            iteration = self.status.iteration()
        stats = {
            'relaxed': int(iteration.counter),
            'selected': len(iteration.mappings),
            'time': '{:.5f}'.format(float(iteration.time_sum)),
            'avg': '{:.5f}'.format(iteration.time_avg()),
        }
        if len(iteration.remaining):
            stats['changes'] = len(iteration.remaining)
        return stats

    def stat_iterations(self):
        stats = {}
        for iteration in self.status.iterations:
            stats[iteration.index] = self.stat_iteration(iteration)
        time = sum(it.time_sum for it in self.status.iterations)
        stats['sum'] = '{:.2f} sec.'.format(time)
        return stats

    def stat_total(self):
        stats = {}
        stats['sum'] = sum(it.time_sum for it in self.status.iterations)
        return stats

    # Also include config information!
    def stat_final(self):
        stats = {'title': 'value'}

        # WordNets
        wordnets = {'source': self.status.source_wn()}
        if self.status.source_wn() != self.status.target_wn():
            wordnets['target'] = self.status.target_wn()
        for key, wordnet in wordnets.items():
            stats.update({
                key: wordnet.name_full(),
                key + ' type': wordnet.uid(),
                key + ' lang': wordnet.lang(),
                key + ' synsets': wordnet.count_synsets(),
                key + ' lunits': wordnet.count_lunits(),
                key + ' uniq lemmas': wordnet.count_lemmas(),
                # Hiper/hypo relations
            })

        # Mapping
        cand = list(self.status.candidates.items())
        counts = np.array([len(node[1]) for node in cand])
        source_syns = self.status.source_wn().count_synsets()
        no_translations = [synset.uid() for synset in self.status.source_wn().all_synsets()
                           if synset.uid() not in self.status.candidates]

        no_candidates = [source_id for source_id in self.status.polysemous if
                         source_id not in self.status.relaxed]

        # Graph with how many of how many
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
        avg = '{:.5f}'.format(avg / len(candidates))

        # Coverage
        manual, d_missing = self.status.manual, self.status.config.manual_missing()

        # Accuracy, monosemous, polysemous
        # Use distance later!
        correct = sum(target_id == self.status.manual.get(source_id, set())
                      for source_id, target_id in self.status.relaxed.items())
        incorrect = len(self.status.relaxed) - correct
        # Perfect, partial, false
        accuracy = '{:.4f}%'.format(correct * 100 / len(self.status.relaxed)
                                    if self.status.relaxed else 0)

        # Dictionary
        translater = self.status.config.translater()

        stats.update({
            'n_nodes': len(self.status.candidates),
            'n_labels': sum(counts),
            'labels_max': max_,
            'labels_avg': avg,
            'manual': len(manual),
            'manual_missing': len(d_missing),
            'n_source_syn': source_syns,
            'n_no_translations': len(no_translations),
            'n_lemmas_dicts': len(self.status.config.dicts()),
            'n_monosemous': len(self.status.monosemous),
            'n_polysemous': len(self.status.polysemous),
            'relaxed': len(self.status.relaxed),
            'n_no_connections': len(no_candidates),
            'correct': correct,
            'incorrect': incorrect,
            'accuracy': accuracy,
            's_trans': translater.s_trans,
            'd_lemma_match': translater.d_lemma_match,
            'd_syn_match': translater.d_syn_match,
            'dict_no_alpha': translater.no_alpha,
            'dict_space or dash': translater.multi,
            'dict_dash': translater.has_dash,
            'dict_digits': translater.has_digits,
        })
        stats.update(self.stat_iterations())
        return stats

    def stat_wordnets(self):
        stats = {}
        wordnets = {'source': self.status.source_wn()}
        if self.status.source_wn() != self.status.target_wn():
            wordnets['target'] = self.status.target_wn()
        for key, wordnet in wordnets.items():
            stats.update({
                key: wordnet.name_full(),
                key + ' type': wordnet.uid(),
                key + ' lang': wordnet.lang(),
                key + ' synsets': wordnet.count_synsets(),
                key + ' lunits': wordnet.count_lunits(),
                key + ' uniq lemmas': wordnet.count_lemmas(),
                # Hiper/hypo relations
            })

    def create_report(self, file):
        writer = csv.writer(file, delimiter='\t')
        writer.writerows(self.stat_final().items())
