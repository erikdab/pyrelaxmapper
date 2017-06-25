# -*- coding: utf-8 -*-


# Should be passed a dict from the parser! (empty if non)
class Constraint:
    """A single constraint to be used in Relaxation labeling.

    Parameters
    ----------
    orig : pyrelaxmapper.wordnet.WordNet
    dest : pyrelaxmapper.wordnet.WordNet
    weights : dict
    """
    def __init__(self, orig, dest, weights):
        self.orig = orig
        self.dest = dest
        self.weights = weights

    def apply(self, mapped, node):
        """Apply constraint to node.

        Parameters
        ----------
        mapped : dict of int
        node : pyrelaxmapper.status.Node
        """
        pass

    def uid(self):
        pass

    @staticmethod
    def isconstraint(constraint):
        pass
