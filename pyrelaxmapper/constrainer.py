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
    cnames : list of str
    cweights : dict
    """

    def __init__(self, cnames, cweights):
        self.constraints = []
        self.ctypes = self.CONSTRAINTS[:]
        self.add_constraints(cnames, cweights)

    CONSTRAINTS = [HHConstraint]

    def add_constraints(self, cnames, cweights):
        """Parse and add constraints.

        Returns
        -------
        cnames : list of str
        cweights : dict
        """
        if not cnames:
            return
        for ctype in self.ctypes:
            cnames_ = ctype.cnames_all()
            match = cnames_.intersection(cnames)
            if match:
                cweights_ = cweights.get(ctype.uid(), {})
                self.constraints.append(ctype(match, cweights_))

    def apply(self, status, node):
        """Apply constraints to node.

        Parameters
        ----------
        status : pyrelaxmapper.status.Status
        node : pyrelaxmapper.status.Node
        """
        for constraint in self.constraints:
            constraint.apply(status, node)
