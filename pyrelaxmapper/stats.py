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

    def stat_performance(self):
        # cache vs. live
        stats = {
            'cache': 0,
            'live': 0
        }
        return stats

    def stat_iteration(self, iteration=None, full=False):
        if not iteration:
            iteration = self.status.iteration()
        key = 'iteration'
        stats = {
            'relaxed': int(iteration.count[key]),
            'selected': len(iteration.mappings),
            # 'changes': len(iteration.remaining),
            'time': '{:.5f}'.format(float(iteration.time_sum[key])),
            'avg': '{:.5f}'.format(iteration.avg(key)),
        }
        if len(iteration.remaining):
            stats['changes'] = len(iteration.remaining)
        if full:
            for key in iteration.time.keys():
                if key == 'iteration':
                    continue
                stats.update({
                    key + ' time': '{:.5f}'.format(float(iteration.time_sum[key])),
                    key + ' count': iteration.count[key],
                    key + ' time_avg': '{:.5f}'.format(iteration.avg(key)),
                })
        return stats

    def stat_iterations(self):
        stats = {}
        for iteration in self.status.iterations:
            stats[iteration.index] = self.stat_iteration(iteration)
        time = sum(it.time_sum['iteration'] for it in self.status.iterations)
        stats['sum'] = '{:.2f} sec.'.format(time)
        return stats

    def stat_total(self):
        stats = {}
        stats['sum'] = sum(it.time_sum['iteration'] for it in self.status.iterations)
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
        # counts_max = counts.argsort()[-5:][::-1]
        # most_ambiguous = '\t'.join([
        #     ','.join([str(cand[idx][0]), str(len(cand[idx][1])),
        #                str(next(
        #                    self.status.config.source_wn().synset(cand[idx][0]).lemma_names()))])
        #     for idx in counts_max])
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
        manual, d_missing = self.status.manual, self.status.d_missing

        # Accuracy, monosemous, polisemous
        # Use distance later!
        correct = sum(target_id == self.status.manual.get(source_id, None)
                      for source_id, target_id in self.status.relaxed.items())
        incorrect = len(self.status.relaxed) - correct
        accuracy = '{:.4f}%'.format(correct * 100 / len(self.status.relaxed)
                                    if self.status.relaxed else 0)

        # Dictionary
        stats.update({
            # Distribution graph!
            'n_nodes': len(self.status.candidates),
            'n_labels': sum(counts),
            'labels_max': max_,
            # 'labels_min': min_,
            'labels_avg': avg,
            # 'most_ambiguous': most_ambiguous,
            # 'n_connections_per_type': 0,
            # 'n_stable': 0,
            # 'n_completed': 0,
            'manual': len(manual),
            'manual_missing': len(d_missing),
            'n_source_syn': source_syns,
            'n_no_translations': len(no_translations),
            's_lemma_coverage': self.status.s_lemma_coverage,
            'd_lemma_coverage': self.status.d_lemma_coverage,
            # Consider just keeping this value in stats or in config or sth
            'n_lemmas_dicts': len(self.status.config.dicts()),
            'n_monosemous': len(self.status.monosemous),
            'n_polysemous': len(self.status.polysemous),
            'relaxed': len(self.status.relaxed),
            'n_no_connections': len(no_candidates),
            'correct': correct,
            'incorrect': incorrect,
            'accuracy': accuracy,
        })

        stats.update(self.stat_iterations())
        return stats

    def create_report(self, file):
        writer = csv.writer(file, delimiter='\t')
        writer.writerows(self.stat_final().items())
