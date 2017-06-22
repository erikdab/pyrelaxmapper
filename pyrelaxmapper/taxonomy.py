# -*- coding: utf-8 -*-
# from igraph import Graph
import numpy as np


class Mapping:
    pass
    # source
    # target
    # nodes (contain labels), weights are per iteration
    # mapped
    # remaining
    # some information about them could change per iteration, some stays over longer


class Node:
    """RL Label between source unit and target candidate

    Parameters
    ----------
    vertex
    """

    def __init__(self, source, labels, weights=None):
        self._source = source
        self._labels = labels
        if weights is None:
            self.reset_weights()
        else:
            self._weights = weights

    def reset_weights(self):
        self._weights = np.ones(len(self._labels)) * self.avg_weight()

    def source(self):
        return self._source

    def labels(self):
        return self._labels

    def weights(self):
        return self._weights

    def avg_weight(self):
        return 1 / len(self._labels)

    def add_weight(self, idx, weight):
        if idx not in self._labels:
            raise KeyError('Node {} does not contain label of id: {}'.format(
                self._source.id_(), idx))
        decr = weight / len(self._labels)
        self._weights[idx] += weight
        self._weights[:idx] -= decr
        self._weights[idx:] -= decr


# Seperate source taxonomy from source + target labels
# def make_taxonomy(source_wn, candidates):
#     """
#
#     Parameters
#     ----------
#     source_wn : pyrelaxmapper.wnmap.wnsource.RLWordNet
#     """
#     # g = Graph(directed=True)
#     # ids could repeat! if we have both orig and dest.
#     # We can have label: wn_shortname_lower
#     g = Graph(directed=True)
#     # Add plWN synsets.
#     # d = map(str, candidates.keys())
#     # g.add_vertices(d)
#     # Entire plWN structure:
#     vertices = (str(synset.id_()) for synset in source_wn.all_synsets())
#     g.add_vertices(vertices)
#     # How to set hipernymy / hiponymy labels
#     hypo_tuples = ((str(source), str(target.name()))
#                    for source, targets in source_wn.all_hyponyms()
#                    for target in targets)
#     hypo_edges = g.add_edges(hypo_tuples)
#
#     hyper_tuples = ((str(source), str(target.name()))
#                     for source, targets in source_wn.all_hypernyms()
#                     for target in targets)
#     hyper_edges = g.add_edges(hyper_tuples)
#
#     # Add PWN synsets.
#     # labels
#     # targets = set()
#     # for cand in candidates.values():
#     #     targets.update(cand)
#     # w = [str(target) for target in targets]
#     # g.add_vertices(w)
#
#     # Add plWN -> PWN candidates
#     # cand_tuples = [(str(source), str(target))
#     #                for source, targets in candidates.items()
#     #                for target in targets]
#     # cand_edges = g.add_edges(cand_tuples)
#
#     # pruned_vs = g.vs(lambda v: int(v['name']) <= 1000)
#     # g2 = g.subgraph(pruned_vs)
#
#     # roots = (str(synset.id_()) for synset in source_wn.all_synsets()
#     #          if not synset.hypernymy())
#
#     # layout = g.layout_reingold_tilford(root=roots)
#     # layout = g.layout_reingold_tilford(root=list(roots)
#     # layout = g.layout("rt")
#     # visual_style = {}
#     # visual_style['layout'] = layout
#     # visual_style['bbox'] = (500, 500)
#     # visual_style['margin'] = 10
#     # Set colors for nodes and edges (base it off of WordNetLoom
#     # plot(g, **visual_style)
#
#     # g = Graph()
#     # g.as_directed()
#     # g.vs['name'] = ['dog', 'entity', 'table']
#     # g['dog', 'entity'] = 1
#     # g.es['weight'] = 2
#     # g.is_weighted()
#     # subgraph?
#     return g
