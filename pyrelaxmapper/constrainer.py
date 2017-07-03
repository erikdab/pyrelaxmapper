# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger()


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
