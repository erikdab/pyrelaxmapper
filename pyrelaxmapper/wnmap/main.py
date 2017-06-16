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
import conf
import logging
from plwordnet import queries
from plwordnet.plsource import PLWordNet
from pwn.psource import PWordNet
from wnmap import wnutils, wndict
# from wnmap.stats import Statistics
from wnmap.wnconfig import WNConfig
# from igraph import Graph


logger = logging.getLogger()


def find_manual(session, source_wn):
    return [source_wn.synset(row.id_) for row in queries.pwn_mappings(session).all()]


# In relaxmapper_4.0 the replacements are done. Technically not needed!
# Later test with '-' and ' '!
def lemma_dict(source):
    """

    Parameters
    ----------
    source : pyrelaxmapper.wnmap.wnsource.RLWordNet
    """
    lemmas = {}
    for synset in source.synsets_all():
        for lemma in synset.lemmas():
            lemma_name = wnutils.clean(lemma.name())
            lemmas.setdefault(lemma_name, []).append(synset.id_())
    return lemmas


# lang_dict should be a dict!
def find_candidates(source_lemmas, target_lemmas, lang_dict):
    """

    Parameters
    ----------
    source_lemmas : dict
    target_lemmas : dict
    lang_dict : dict
    """
    candidates_dict = {}
    for source_lemma, source_synsets in source_lemmas.items():
        if source_lemma not in lang_dict:
            continue
        translations = lang_dict[source_lemma]
        # THIS WAS SLOW!
        # candidates = [candidate_synset
        #               for lemma, synsets in target_lemmas.items() if lemma in translations
        #               for candidate_synset in synsets]
        # THIS IS FAST!!!! OPTIMIZATION >_<
        candidates = [synset
                      for lemma in translations if lemma in target_lemmas
                      for synset in target_lemmas[lemma]]
        if not candidates:
            continue
        for synset in source_synsets:
            candidates_dict.setdefault(synset, set()).update(candidates)
    return candidates_dict


def make_taxonomy(source_wn):
    # g = Graph()
    # vertices = (str(synset.id_()) for synset in source_wn.synsets_all())
    # g.add_vertices(vertices)
    # # How to set hipernymy / hiponymy labels
    # edges = ((str(source), str(target.name()))
    #          for source, targets in source_wn._hypernyms.items()
    #          for target in targets)
    # hyper_edges = g.add_edges(edges)
    # edges = ((str(source), str(target.name()))
    #          for source, targets in source_wn._hypernyms.items()
    #          for target in targets)
    # hyper_edges = g.add_edges(edges)
    # g = Graph()
    # g.as_directed()
    # g.vs['name'] = ['dog', 'entity', 'table']
    # g['dog', 'entity'] = 1
    # g.es['weight'] = 2
    # g.is_weighted()
    # subgraph?
    pass


class RelaxMapper:
    """Relaxation Labeling WordNet Mapping Main algorithm class."""
    # config


def main():
    # Save these variables in a master class?
    # Params:
    # Config, Clean cache? ENV vars
    # Clean intermediary caches? (Only keep caches necessary for model selection?)
    # 1. Configuration
    config = WNConfig()
    # Print short info:
    # Source / Target / Main settings.
    # 2. Define Source and Target
    # Sources:
    # plsource: Uncached: 13.664 sec. | cached: 2.072 sec. | gain: 6.6X
    # psource:  Uncached: 17.885 sec. | cached: 1.325 sec. | gain: 13.5X
    # Pass the options they need! a config file
    source_cls = PLWordNet
    target_cls = PWordNet
    # Could have short names!
    source_name = source_cls.name_short()
    target_name = target_cls.name_short()
    # OK, NEED TO BE ABLE TO SPECIFY OPTIONS, DIRECTORIES, INSTALLATION, DATABASE SETTINGS
    # Should have a single conf file location! Optional if not needed
    # Also should have additional settings to describe algorithm specific details (like pos)
    source_wn = wnutils.cached('wordnet', source_cls, [conf.make_session()], group=source_name)
    target_wn = wnutils.cached('wordnet', target_cls, group=target_name)
    source_lang = source_wn.lang()
    target_lang = target_wn.lang()

    make_taxonomy(source_wn)

    # 3. Create Dictionaries
    # Morphy, Fuzzy search? Word order not important?
    # GOOD, Function could be placed in rlsource! (rlwordnet)
    # uncached: 0.471 sec. | cached: 0.058 sec. | gain: 8.1X
    source_lemmas = wnutils.cached('(lemmas -> synsets)', lemma_dict, [source_wn],
                                   group=source_name)
    # uncached: 0.394 sec. | cached: 0.047 sec. | gain: 8.3X
    target_lemmas = wnutils.cached('(lemmas -> synsets)', lemma_dict, [target_wn],
                                   group=target_name)

    # Create multi-lingual dictionary (not needed if single-lingual)
    lang_dict_file = '({} -> {}) Dictionary'.format(source_lang, target_lang)
    lang_dict = wnutils.cached(lang_dict_file, wndict.translate)

    # Could have weights for best translations, so so translations!
    candidates_file = '({} -> {}) Candidates'.format(source_name, target_name)
    candidates = wnutils.cached(candidates_file, find_candidates,
                                [source_lemmas, target_lemmas, lang_dict.translated])

    # Find monosemous!
    # monosemous = {source_id: list(target_ids)[0] for source_id, target_ids in candidates.items()
    #               if len(target_ids) == 1}

    polysemous = {source_id: target_ids for source_id, target_ids in candidates.items()
                  if len(target_ids) > 1}

    # Specify manual mappings for performance assessment!
    manual_file = '({} -> {}) Manual'.format(source_name, target_name)
    manual = wnutils.cached(manual_file, find_manual, [conf.make_session(), source_wn])
    # Direction, Target WN Name
    # Could also check both?
    # manual = wnutils.cached(manual_file, source_wn.mappings, [True, target_wn.name()])

    # manual: 40000 / candidates: 42000
    # When using same clean, improved to 49875.
    # ENG has morphy, PL doesn't!
    # Specify training and test sets.
    dataset = [source_wn.synset(synset.id_()) for synset in manual if synset.id_() in polysemous]
    splitter = int(len(dataset)*config.dataset_split())
    training = dataset[:splitter]
    # test = dataset[splitter:]
    print('{}'.format(len(training)))

    # 4. Initialize Algorithm, Stats, Constraints, Relaxer, Taxonomy, etc.
    # stats = Statistics(source_wn, target_wn)
    # Relaxer
    # Constraints

    # Print early statistics

    # 5. Perform relaxation labeling
    # Normalize
    # poly.rl_loop(stats, config)

    # 6. Create reports, visualization, statistics, etc.
    # Graphs
    # Map graph
    # Callbacks to run something. Example insert into DB
    # CSV / XLSX
    # Also print summary to stdout
