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
from plwordnet import queries
from plwordnet.plsource import PLWordNet
from pwn.psource import PWordNet
from wnmap import wnutils, wndict, mono, poly
from wnmap.stats import Statistics
from wnmap.wnconfig import WNConfig


def already_mapped(session):
    return queries.pwn_mappings(session).all()


def main():
    config = WNConfig()
    dictionary = wnutils.cached('dictionary2', wndict.translate)
    # Uncached: 13.664 sec., cached: 2.072 sec.
    source = wnutils.cached('plsource', PLWordNet, [conf.make_session()])
    # Uncached: 17.885 sec., cached: 1.325 sec.
    target = wnutils.cached('psource', PWordNet)

    already = wnutils.cached('already', already_mapped, [conf.make_session()])
    to_map = [source.synset(row.id_) for row in already][:1000]

    stats = Statistics(source, target, to_map, dictionary)

    mono.mono(stats)
    poly.rl_loop(stats, config)
