# -*- coding: utf-8 -*-


class Stats:
    def __init__(self, status):
        self.status = status
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

    def mapping_stats(self):
        # logger.info('remaining {}; no translations {}; translated: {}, using weights: {}'
        #             .format(remaining_c, not_translated, translated, using_weights))
        # logger.info('no_translations: {}, no_translations_lu: {}'
        #             .format(len(no_translations), len(no_translations_lu)))
        pass

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

    def stats_iteration(self):
        pass
        # logger.info("time: {}".format(toc - tic))
        # logger.info("Suggestions: {}".format(suggestions))
        # logger.info("Accepted by user: {}".format(selected))
        # logger.info("Selected by algorithm: {}".format(mapped_count))
