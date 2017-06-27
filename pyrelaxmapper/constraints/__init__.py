# -*- coding: utf-8 -*-


class Constraint:
    """A single constraint to be used in Relaxation labeling.

    Parameters
    ----------
    cnames : list of str
    cweights : dict
    """
    def __init__(self, cnames, cweights):
        self.cnames = cnames
        self.cweights = cweights

    def apply(self, status, node):
        """Apply constraints to node.

        Parameters
        ----------
        status : pyrelaxmapper.status.Status
        node : pyrelaxmapper.status.Node
        """
        pass

    @staticmethod
    def uid():
        """Constraint uid."""
        pass

    @staticmethod
    def cnames_all():
        """Names of constraints which this constraint contains.

        Returns
        -------
        set of str
        """
        pass
