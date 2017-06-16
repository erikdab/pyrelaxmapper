# -*- coding: utf-8 -*-
"""Relaxation labeling Configuration."""


class WNConfig:
    """Relaxation Labeling Configuration.

    * Source, Target
    * Translator
    * Clean function
    * Keep only caches needed for model selection.
    * Keep caches only in temporary folder (dropped on system reboot)
    * Inserter (inserts mapping results somewhere)
    * POS
    * empties (empty synsets?)
    * include monosemous?
    * graph directory
    * Constraints, constraint weights
    * Should be possible to change most settings here, instead of creating a Python file.
    """

    def __init__(self):
        self.constrains = 'ii'
        # self.cache = True
        self._pos = ['n']
        self._dataset_split = 0.8
        pass

    def pos(self):
        return self._pos

    def dataset_split(self):
        return self._dataset_split

    def open(self):
        pass

    def save(self):
        pass

    def source(self):
        """Specification of mapping source."""
        pass

    def target(self):
        """Specification of mapping target."""
        pass

    def cache(self):
        pass
