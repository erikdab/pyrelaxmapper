# -*- coding: utf-8 -*-
import logging

from pyrelaxmapper.constraints.hh import HHConstraint

logger = logging.getLogger()


# Is there a way to constrain first some things and use
# some WSD to decrease the nr of candidates?
# That would speed up tremendously.
# TODO: Fast evaluate.
# TODO: Setup constraints from conf file.
# In future may need to be cached if it will be too slow,
# but remember to not cache the wordnets!
class Constrainer:
    """Relaxation labeling constrainer.

    Parameters
    ----------
    orig : pyrelaxmapper.wordnet.WordNet
    dest : pyrelaxmapper.wordnet.WordNet
    constraints : list of str
    constr_weights : dict
    """

    def __init__(self, orig, dest, constraints, constr_weights):
        self.orig = orig
        self.dest = dest
        self._constr = []
        # self._constr_str = constraints
        # self._constr_types = self.CONSTRAINTS[:]
        # self._constr_weights = constr_weights
        self._setup_constraints()

    # CONSTRAINTS = [HyperHypoConstraint, WordsConstraint, GlossConstraint,
    #                DaughtersConstraint]

    def _setup_constraints(self):
        # constr_str = self._constr_str
        # if not constr_str:
        #     return
        # constr_weights = self._constr_weights
        # for constr_uid in constr_str:
        #     for constr_cls in self._constr_types:
        #         if constr_cls.isconstraint(constr_uid):
        #             self._constr.append(constr_cls(constr_uid, constr_weights[constr_uid]))
        # self._constr.append(HyperHypoConstraint(self.orig, self.dest, {}))
        self._constr.append(HHConstraint(self.orig, self.dest, {}))

    def apply(self, mapped, node):
        """Apply constraints to node.

        Parameters
        ----------
        mapped : dict
        node : list of Node
        """
        for constraint in self._constr:
            constraint.apply(mapped, node)
