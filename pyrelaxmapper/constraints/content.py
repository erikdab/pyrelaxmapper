# -*- coding: utf-8 -*-
from pyrelaxmapper.constraints import Constraint


class WordsConstraint(Constraint):
    RW = 0.1
    EMPTYITEMSWEIGHT = 0.5

    def apply(self, mapped, node):
        power_match = False
        self.dictionary = {}
        source = self.orig.synset(node.source())
        source_lemmas = source.lemma_names()
        source_translations = (lemma for source_lemma in source_lemmas
                               for lemma in self.dictionary[source_lemma])

        for idx, target_name in enumerate(node.labels()):
            target = self.dest.synset(target_name)
            target_lemmas = target.lemma_names()

            # Count of matches
            m = sum(lemma in source_translations for lemma in target_lemmas)

            # Power matches
            if power_match:
                # How close are the synsets
                f = len(source_lemmas) + len(target_lemmas) - 2 * m
                if m + f != 0:
                    weight = self.RW * (m ** 3 / (m + f) ** 2)
                else:
                    weight = self.EMPTYITEMSWEIGHT
            else:
                weight = m * self.RW

            node.add_weight(idx, weight)


class GlossConstraint(Constraint):
    def apply(self, mapped, node):
        pass
