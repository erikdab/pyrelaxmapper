# -*- coding: utf-8 -*-
"""
1. Specify config, settings, data directories, destionations, etc.
2. Verify config, data directories, all data is accessible (database connection works), etc.
3. Process any data, cache everything needed (possible)
4. Create Statistics, Translater, Dicts (if required)
    * Use morphy and similar tools, fuzzy search, whichever is needed. Specify this in
        * config.

    * Find Potentials (translate or if same language it's easier.
    * Find monosemous
    * Use things like Occurence counting to filter out.
5. Relaxation labeling algorithm.
6. Statistics, graphs, excel documents, visualizations, etc.
"""
import logging
from wnmap import wnutils, translate, wnsource
from wnmap.taxonomy import Node

logger = logging.getLogger()


# Stats could be a part of this.
class RelaxMapper:
    """Relaxation Labeling WordNet Mapping Main algorithm class.

    Parameters
    ----------
    config : pyrelaxmapper.wnmap.wnconfig.WNConfig
    constrainer : pyrelaxmapper.wnmap.constraint.Constrainer, optional
    """
    def __init__(self, config, constrainer=None):
        self.config = config
        self.orig = config.source_wn()
        self.dest = config.target_wn()
        self.constrainer = constrainer
        self._lang_dict = None
        self._candidates = None
        self._monosemous = None
        self._polysemous = None
        self._nodes = {}
        self.cached()

    def candidates(self):
        if self._candidates:
            return self._candidates
        orig_lemmas = wnutils.cached('(lemmas -> synsets)', self.orig.lemma_synsets,
                                     group=self.orig.name())
        # uncached: 0.394 sec. | cached: 0.047 sec. | gain: 8.3X
        dest_lemmas = wnutils.cached('(lemmas -> synsets)', self.dest.lemma_synsets,
                                     group=self.dest.name())

        lang_dict_file = '({} -> {}) Dictionary'.format(self.orig.lang(), self.dest.lang())
        self._lang_dict = wnutils.cached(lang_dict_file, translate.translate)

        # Could have weights for best translations
        candidates_file = '({} -> {}) Candidates'.format(self.orig.name(), self.dest.name())
        self._candidates = wnutils.cached(candidates_file, wnsource.find_candidates,
                                          [orig_lemmas, dest_lemmas, self._lang_dict.translated])
        return self._candidates

    def monosemous(self):
        return self._monosemous

    def polysemous(self):
        return self._polysemous

    def lang_dict(self):
        return self._lang_dict

    def cached(self):
        # Intermediary, not necessary to save.
        candidates_file = '({} -> {}) Candidates'.format(self.orig.name(), self.dest.name())
        self._candidates = wnutils.cached(candidates_file, self.candidates)

        self._monosemous = {source_id: target_ids for source_id, target_ids in
                            self._candidates.items() if len(target_ids) == 1}
        self._polysemous = {source_id: Node(source_id, target_ids) for source_id, target_ids in
                            self._candidates.items() if len(target_ids) > 1}


def main():
    pass
    # Place this inside commands!
    # config = WNConfig(conf.config)
    # source_cls = PLWordNet
    # target_cls = PWordNet
    # source_wn = wnutils.cached('wordnet', source_cls, [conf.config],
    #                            group=source_cls.name())
    # target_wn = wnutils.cached('wordnet', target_cls, group=target_cls.name())
    #
    # constrainer = Constrainer(source_wn, target_wn, ['ii'])
    #
    # relaxmapper = RelaxMapper(config, source_wn, target_wn, constrainer)
    # stats = Statistics(relaxmapper)
    # d = len(stats.mappings)
    # logger.info('Mappings: {}'.format(len(stats.mappings)))
    # relaxer.rl_loop(stats)
    # d2 = len(stats.mappings)
    # logger.info('It Mappings: {}'.format(stats.iteration().mappings))
    # logger.info('Mappings: {}, {}'.format(d, d2))
    # 1. Configuration
    # config = WNConfig()
    # Print short info:
    # Source / Target / Main settings.
    # 2. Define Source and Target
    # Sources:
    # plsource: Uncached: 13.664 sec. | cached: 2.072 sec. | gain: 6.6X
    # psource:  Uncached: 17.885 sec. | cached: 1.325 sec. | gain: 13.5X
    # Pass the options they need! a config file
    # source_cls = PLWordNet
    # target_cls = PWordNet
    # Could have short names!
    # source_name = source_cls.name_short()
    # target_name = target_cls.name_short()
    # OK, NEED TO BE ABLE TO SPECIFY OPTIONS, DIRECTORIES, INSTALLATION, DATABASE SETTINGS
    # Should have a single conf file location! Optional if not needed
    # Also should have additional settings to describe algorithm specific details (like pos)
    # source_wn = wnutils.cached('wordnet', source_cls, [conf.make_session()], group=source_name)
    # target_wn = wnutils.cached('wordnet', target_cls, group=target_name)
    # source_lang = source_wn.lang()
    # target_lang = target_wn.lang()

    # 3. Create Dictionaries
    # Morphy, Fuzzy search? Word order not important?
    # GOOD, Function could be placed in rlsource! (rlwordnet)
    # uncached: 0.471 sec. | cached: 0.058 sec. | gain: 8.1X
    # source_lemmas = wnutils.cached('(lemmas -> synsets)', lemma_dict, [source_wn],
    #                                group=source_name)
    # # uncached: 0.394 sec. | cached: 0.047 sec. | gain: 8.3X
    # target_lemmas = wnutils.cached('(lemmas -> synsets)', lemma_dict, [target_wn],
    #                                group=target_name)

    # Create multi-lingual dictionary (not needed if single-lingual)
    # lang_dict_file = '({} -> {}) Dictionary'.format(source_lang, target_lang)
    # lang_dict = wnutils.cached(lang_dict_file, wndict.translate)

    # Could have weights for best translations, so so translations!
    # candidates_file = '({} -> {}) Candidates'.format(source_name, target_name)
    # candidates = wnutils.cached(candidates_file, find_candidates,
    #                             [source_lemmas, target_lemmas, lang_dict.translated])

    # Find monosemous!
    # monosemous = {source_id: list(target_ids)[0] for source_id, target_ids in candidates.items()
    #               if len(target_ids) == 1}
    #
    # polysemous = {source_id: target_ids for source_id, target_ids in candidates.items()
    #               if len(target_ids) > 1}

    # Specify manual mappings for performance assessment!
    # manual_file = '({} -> {}) Manual'.format(source_name, target_name)
    # manual = wnutils.cached(manual_file, find_manual, [conf.make_session(), source_wn])
    # manual_str = [synset.id_() for synset in manual]
    # Direction, Target WN Name
    # Could also check both?
    # manual = wnutils.cached(manual_file, source_wn.mappings, [True, target_wn.name()])

    # manual: 40000 / candidates: 42000
    # When using same clean, improved to 49875.
    # ENG has morphy, PL doesn't!
    # Specify training and test sets.
    # dataset = [source_wn.synset(synset.id_()) for synset in manual if synset.id_() in polysemous]
    # splitter = int(len(dataset) * config.dataset_split())
    # training = dataset[:splitter]
    # # test = dataset[splitter:]
    # print('{}'.format(len(training)))

    # nodes = [Node(source, targets) for source, targets in polysemous.items()]

    # training_cand = {source: targets for source, targets in polysemous.items()
    #                  if source in manual_str}
    # taxonomy_file = '({} -> {}) Taxonomy'.format(source_name, target_name)
    # taxonomy = wnutils.cached(taxonomy_file, make_taxonomy,
    #                           [source_wn, polysemous])
    # make_taxonomy(source_wn, polysemous)

    # 4. Initialize Algorithm, Stats, Constraints, Relaxer, Taxonomy, etc.
    # stats = Statistics(source_wn, target_wn)
    # Relaxer
    # Constraints

    # Print early statistics

    # 5. Perform relaxation labeling
    # relaxer.rl_loop(stats, config)
    # Normalize
    # poly.rl_loop(stats, config)

    # 6. Create reports, visualization, statistics, etc.
    # Graphs
    # Map graph
    # Callbacks to run something. Example insert into DB
    # CSV / XLSX
    # Also print summary to stdout
