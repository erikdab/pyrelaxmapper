# -*- coding: utf-8 -*-
"""HyperHypo Constraint functionality."""
import logging
from collections import defaultdict
from enum import Enum

import numpy as np

from pyrelaxmapper import utils
from pyrelaxmapper.constraints import Constraint

logger = logging.getLogger()


# TODO: Init from config file.
# TODO: Use only HHType to speed up hashing!
class HHConstraint(Constraint):
    """Constraints which utilize hyper/hyponym connections."""

    def __init__(self, orig, dest, weights):
        super().__init__(orig, dest, weights)
        # codes = ['ii', 'aa', 'ai', 'ia']
        codes = ['ii']
        # Anything better?
        self.rel_weight = {HHDirection.hyper: 1.0, HHDirection.hypo: 0.93}
        self.hhtypes = [hhtype for code in set(codes) for hhtype in HHType.factory(code)]
        self.o_any_recurse, self.d_any_recurse = _any_recurse(self.hhtypes)

    # Relation_uids takes some time.
    # Searching for mappings in the mapped dict is the slowest.
    # connections iterate over iterations (could be maybe improved)
    # HEY! USE lru_cache() for hashing?
    # Hashing used to take longer, now I "cached" the hash
    # Calculating weights isn't super fast either.
    # Convert 10 constraints to HHType!? Maybe, COULD BE DONE! maybe drop the other enums?
    def apply(self, mapped, node):
        o_any_recurse, d_any_recurse, rel_weight, hhtypes = (
            self.o_any_recurse, self.d_any_recurse, self.rel_weight, self.hhtypes)

        avg_labels = 10 / (node.count() ** 2)
        o_hyper, o_hypo = _relation_uids(self.orig.synset(node.source()), o_any_recurse)

        for idx, label in enumerate(node.labels()):
            d_hyper, d_hypo = _relation_uids(self.dest.synset(label), d_any_recurse)
            conn = {
                HHDirection.hyper: _connections(mapped, o_hyper, d_hyper),
                HHDirection.hypo: _connections(mapped, o_hypo, d_hypo)
            }
            weight = np.sum(
                _weight(node, hhtype, conn, rel_weight, node.avg_weight(), avg_labels)
                for hhtype in hhtypes
            )
            node.add_weight(idx, weight)


#######################################################################
# HH Types


class HHRecurse(Enum):
    """HyperHypo Constraint Recurse Enum."""
    recurse = 'a'
    immediate = 'i'


class HHDirection(Enum):
    """HyperHypo Constraint Direction Enum."""
    hyper = 'e'
    hypo = 'o'
    both = 'b'


class HHType:
    """HyperHypo Constraint Type.

    Parameters
    ----------
    o_recurse : HHRecurse
    d_recurse : HHRecurse
    direction : HHDirection
    """

    def __init__(self, o_recurse=None, d_recurse=None, direction=None):
        self.o_recurse = o_recurse
        self.d_recurse = d_recurse
        self.direction = direction
        self._cache_full = hash(
            '{}{}{}'.format(o_recurse, d_recurse, direction if direction else ''))
        self._cache_recurse = hash('{}{}'.format(self.o_recurse, self.d_recurse))

    def __str__(self):
        return 'HHType({},{},{})'.format(self.o_recurse.value,
                                         self.d_recurse.value,
                                         self.direction.value if self.direction else '')

    def __hash__(self):
        if self.direction:
            return self._cache_full
        else:
            return self._cache_recurse
            # return hash((self.o_recurse, self.d_recurse, self.direction))

    def recurse_hash(self):
        """A hash of only the recurse information."""
        return self._cache_recurse

    @staticmethod
    def factory(code, require_direction=True):
        """Create HyperHypo types from string.

        If direction is absent, creates all three directions.

        Parameters
        ---------
        code : str
        require_direction : bool

        Returns
        -------
        list of HHCode
        """
        try:
            o_recurse = utils.enum_factory(HHRecurse, code[0])[0]
            d_recurse = utils.enum_factory(HHRecurse, code[1])[0]
        except KeyError:
            raise KeyError('HHCode requires 2 chars')

        if len(code) == 3:
            directions = utils.enum_factory(HHDirection, code[2])
        elif require_direction:
            directions = [HHDirection.hyper, HHDirection.hypo, HHDirection.both]
        else:
            directions = [None]

        return [HHType(o_recurse, d_recurse, direction) for direction in directions]


#######################################################################
# HH Functions

def _relation_uids(synset, any_recurse):
    """Get synset hypernym and hyponym relation uids.

    Parameters
    ----------
    synset : pyrelaxmapper.wordnet.Synset
    any_recurse : dict of HHDirection, bool
        Whether any HHType utilizes recursive searching.
        If only immediate, returns only the first layer for speedups.

    Returns
    -------
    tuple
    """
    hyper_range = None if any_recurse[HHDirection.hyper] else 1
    hypo_range = None if any_recurse[HHDirection.hyper] else 1
    hyper = synset.hypernym_layers(True)[:hyper_range]
    hypo = synset.hyponym_layers(True)[:hypo_range]
    return hyper, hypo


def _any_recurse(hhtypes):
    """Checks whether any hhtype recurses on hyper or hypo.

    Isn't beautiful, but only runs once, so speed is irrelevant.

    Returns
    -------
    tuple
    """
    o_recurse = {
        HHDirection.hyper:
            any(hhtype.o_recurse == HHRecurse.recurse for hhtype in hhtypes
                if hhtype.direction in [HHDirection.hyper, HHDirection.both]),
        HHDirection.hypo:
            any(hhtype.o_recurse == HHRecurse.recurse for hhtype in hhtypes
                if hhtype.direction in [HHDirection.hypo, HHDirection.both]),
    }
    d_recurse = {
        HHDirection.hyper:
            any(hhtype.d_recurse == HHRecurse.recurse for hhtype in hhtypes
                if hhtype.direction in [HHDirection.hyper, HHDirection.both]),
        HHDirection.hypo:
            any(hhtype.d_recurse == HHRecurse.recurse for hhtype in hhtypes
                if hhtype.direction in [HHDirection.hypo, HHDirection.both]),
    }
    return o_recurse, d_recurse


msg = {}


def message(o_layer, d_layer, num):
    """Print statistical messages."""
    if msg.get(num):
        return
    msg[num] = True
    lens = '[{},{}]'.format(len(o_layer), len(d_layer))
    diff = 'equal' if len(o_layer) == len(d_layer) else 'diff'
    count = any(o_id == d_id for o_id in o_layer for d_id in d_layer)
    logger.info('#{} len:{} {} any:{}'.format(num, lens, diff, count))


def _connection_stats(o_layer, d_layer, count):
    # Write this up for Statistics
    if len(o_layer) == len(d_layer) == 1:
        if count:
            message(o_layer, d_layer, 0)
        else:
            message(o_layer, d_layer, 1)
    elif len(o_layer) == len(d_layer):
        if count:
            message(o_layer, d_layer, 2)
        if not count:
            message(o_layer, d_layer, 3)
    if len(o_layer) != len(d_layer):
        if min(len(o_layer), len(d_layer)) > 1:
            if count:
                message(o_layer, d_layer, 4)
            if not count:
                message(o_layer, d_layer, 5)
        else:
            if count:
                message(o_layer, d_layer, 6)
            if not count:
                message(o_layer, d_layer, 7)


_hhtype = {hhtype: hash(HHType.factory(hhtype, False)[0]) for hhtype in
           ['ii', 'iib', 'ia', 'iab', 'ai', 'aib', 'aa', 'aab']}


def get_o_mapped(mapped, o_layer):
    """Get mapped synsets."""
    return {mapped.get(o_syn, 0) for o_syn in o_layer}


def count_conn(o_mapped, d_layer):
    """Count connections."""
    return sum(d_syn in o_mapped for d_syn in d_layer)


def _connections(mapped, orig_rel, dest_rel):
    """Find existing connections between source and labels.

    Parameters
    ----------
    mapped
        Already mapped synsets.
    orig_rel : list
        Origin relation layers. (can be hyper/hypo)
    dest_rel : list
        Destination relation layers. (can be hyper/hypo)

    Returns
    -------
    defaultdict
    """
    conn = defaultdict(lambda: defaultdict(int))
    max_dist_sum = 0
    for o_dist, o_layer in enumerate(orig_rel):
        o_mapped = get_o_mapped(mapped, o_layer)
        for d_dist, d_layer in enumerate(dest_rel):
            count = count_conn(o_mapped, d_layer)

            if not count:
                continue

            dist_max, dist_sum = max([o_dist, d_dist]), (o_dist + d_dist)
            if o_dist == d_dist == 0:
                conn[_hhtype['ii']][dist_max] += count
                conn[_hhtype['iib']][dist_sum] += count
            if o_dist == 0:
                conn[_hhtype['ia']][dist_max] += count
                conn[_hhtype['iab']][dist_sum] += count
            if d_dist == 0:
                conn[_hhtype['ai']][dist_max] += count
                conn[_hhtype['aib']][dist_sum] += count
            conn[_hhtype['aa']][dist_max] += count
            conn[_hhtype['aab']][dist_sum] += count

            if max_dist_sum < dist_sum:
                max_dist_sum = dist_sum
    conn['dist_sum'][0] = max_dist_sum

    return conn


def _weight_formula(weight, dist_count):
    """Calculate weight formula

    Parameters
    ----------
    weight : float
    dist_count
        generator of (distance, count)

    Returns
    -------
    float
    """
    return np.sum(count * (weight / 2 ** distance) for distance, count in dist_count)


def _weight(node, code, conn, rel_weights, avg_weight, avg_candidates):
    """Apply constraint to calculate weight.

    Parameters
    ----------
    node : pyrelaxmapper.status.Node
    code : HHType
    conn
    rel_weights : dict
    avg_weight : float
    avg_candidates : float

    Returns
    -------
    float
    """
    direction = code.direction
    if direction in [HHDirection.hyper, HHDirection.hypo]:
        recurse = code.recurse_hash()
        weight = rel_weights[direction] * avg_weight
        dist_count = conn[direction][recurse].items()

    elif direction == HHDirection.both:
        h = hash(code)
        e = conn[HHDirection.hyper]
        o = conn[HHDirection.hypo]
        e_ = e[h]
        o_ = o[h]
        if not e_ or not o_:
            return 0.0

        weight = 2. * avg_candidates
        # Hypernyms are less important, so we take only their max_dist,
        # but count all hyponyms
        hyper_dist_sum = e['dist_sum'][0]
        dist_count = ((hyper_dist_sum + hypo_dist_sum, count) for
                      hypo_dist_sum, count in o_.items())
        # hyper_dist_sum = conn[HHDirection.hyper]['dist_sum']
        # dist_count = ((hyper_dist_sum + hypo_dist_sum, count) for
        #               hypo_dist_sum, count in conn[HHDirection.hypo][code].items())
    else:
        return 0.0
    return _weight_formula(weight, dist_count)
