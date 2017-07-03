# -*- coding: utf-8 -*-
from pyrelaxmapper.constraints import Constraint


class DaughtersConstraint(Constraint):
    RDAUGHTERS = 0.1

    class Policy:
        NONE = 0
        ZERO = 1
        EQUAL = 2
        DIFF = 3

    def apply(self, status, node):
        orig = status.source_wn()
        dest = status.target_wn()
        policy = self.Policy.NONE
        source = orig.synset(node.source)
        source_hipo = len(source.hiponyms())

        for idx, target_name in enumerate(node.labels):
            target = dest.synset(target_name)
            target_hypo = len(target.hyponyms())

            weight = 0
            if policy == self.Policy.ZERO and source_hipo == 0 and target_hypo == 0:
                weight = self.RDAUGHTERS
            elif policy == self.Policy.EQUAL and source_hipo == target_hypo:
                weight = self.RDAUGHTERS
            elif policy == self.Policy.DIFF and source_hipo != target_hypo:
                diff = (target_hypo + 0.1) / (source_hipo + 0.1)
                if diff > 1:
                    diff = 1 / diff
                diff = diff ** 0.5
                weight = self.RDAUGHTERS * diff

            if weight:
                node.add_weight(idx, weight)

