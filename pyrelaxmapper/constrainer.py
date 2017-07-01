# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger()


# Is there a way to constrain first some things and use
# some WSD to decrease the nr of candidates?
# That would speed up tremendously.
class Constrainer:
    """Relaxation labeling constrainer.

    Parameters
    ----------
    constraints : Constraint
    """

    def __init__(self, constraints=None):
        if constraints is None:
            constraints = []
        self.constraints = constraints if constraints else []

    def apply(self, status, node):
        """Apply constraints to node.

        Parameters
        ----------
        status : pyrelaxmapper.status.Status
        node : pyrelaxmapper.status.Node
        """
        for constraint in self.constraints:
            constraint.apply(status, node)
