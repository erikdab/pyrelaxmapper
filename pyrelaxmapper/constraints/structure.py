# -*- coding: utf-8 -*-
from pyrelaxmapper.constraints import Constraint

# class AntonymsConstraint(Constraint):
#     def apply(self, mapped, node):
#         source_syn = self.orig(node.source())
#         source_antonyms = source_syn.antonyms()
#
#         for idx, target_name in enumerate(node.labels()):
#             target_syn = self.orig(target_name)
#             target_antonyms = target_syn.antonyms()


class DaughtersConstraint(Constraint):
    RDAUGHTERS = 0.1

    # class Policy(enum.Enum):
    #     NONE = enum.auto()
    #     ZERO = enum.auto()
    #     EQUAL = enum.auto()
    #     DIFF = enum.auto()
    class Policy:
        NONE = 0
        ZERO = 1
        EQUAL = 2
        DIFF = 3

    def apply(self, mapped, remaining):
        policy = self.Policy.NONE
        for node in remaining.items():
            source = self.orig.synset(node.source())
            source_hipo = len(source.hiponyms())

            for idx, target_name in enumerate(node.labels()):
                target = self.dest.synset(target_name)
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


class HyperHypoConstraint(Constraint):
    """
    123
    AAE
    1: Source WN
    2: Target WN
        A - recursive
        I - immediate
    3: Type:
        E - hyper
        O - hypo
        B - both
    """

    # Remove
    def hipo(self, synset):
        """Find hiponyms for synset.

        Parameters
        ----------
        synset : pyrelaxmapper.rlabel.rlsource.RLSynset
            Synset
        """
        todo = [synset]
        hiponyms = []
        hipo_layers = []
        while todo:
            do_next = []
            for node in todo:
                do_next.extend(node.hyponyms())
            todo = do_next
            hiponyms.extend(todo)
            if todo:
                hipo_layers.append(todo)
        children = hipo_layers[0] if hipo_layers else []
        return hiponyms, hipo_layers, children

    def apply(self, mapped, node):
        self.mapped = mapped
        # constr = self.constrainer._constr
        # constr_weights = self.constrainer._constr_weights
        constr = 'ii'
        source = self.orig.synset(node.source())
        hiper_pl = source.hypernym_paths()
        if hiper_pl:
            hiper_pl = hiper_pl[0][::-1][1:]
        hiper_pl = [syn.uid() for syn in hiper_pl]
        fathers_pl = hiper_pl[0] if len(hiper_pl) >= 1 else -1
        hipo_pl, hipo_pl_layers, children_pl = self.hipo(source)
        hipo_pl = [syn.uid() for syn in hipo_pl]
        hipo_pl_layers = [[syn.uid() for syn in layer] for layer in hipo_pl_layers]
        children_pl = [syn.uid() for syn in children_pl]

        weight_hiper = 1.0
        weight_hipo = 0.93
        avg_weight = node.avg_weight()

        # traverse through target potential candidates.
        for idx, target_name in enumerate(node.labels()):
            target_syn = self.dest.synset(target_name)
            hiper_en = target_syn.hypernym_paths()
            if hiper_en:
                hiper_en = hiper_en[0][::-1][1:]
            hiper_en = [syn.uid() for syn in hiper_en]
            fathers_en = hiper_en[0] if len(hiper_en) >= 1 else -1
            hipo_en, hipo_en_layers, children_en = self.hipo(target_syn)
            hipo_en = [syn.uid() for syn in hipo_en]
            hipo_en_layers = [[syn.uid() for syn in layer] for layer in hipo_en_layers]
            children_en = [syn.uid() for syn in children_en]

            if constr in ['iie', 'ii']:
                self.iie(fathers_pl, fathers_en, node, idx, weight_hiper,
                         avg_weight)

            if constr in ['iio', 'ii']:
                self.iio(children_pl, children_en, idx, node, weight_hipo,
                         avg_weight)

            if constr in ['iib', 'ii']:
                self.iib(fathers_pl, fathers_en, children_pl, children_en, idx,
                         node)

            if constr in ['aie', 'ai']:
                self.aie(fathers_en, hiper_pl, avg_weight, weight_hiper, idx, node)

            if constr in ['aio', 'ai']:
                self.aio(hipo_pl, hipo_pl_layers, children_en, avg_weight,
                         weight_hipo, idx,
                         node)

            if constr in ['aib', 'ai']:
                self.aib(hiper_pl, fathers_en, hipo_pl, hipo_pl_layers, children_en,
                         idx,
                         node)

            if constr in ['iae', 'ia']:
                self.iae(fathers_pl, hiper_en, weight_hiper, avg_weight, idx,
                         node)

            if constr in ['iao', 'ia']:
                self.iao(children_pl, hipo_en, weight_hipo, avg_weight,
                         hipo_en_layers,
                         idx, node)

            if constr in ['iab', 'ia']:
                self.iab(fathers_pl, hiper_en, children_pl, hipo_en,
                         weight_hiper,
                         hipo_en_layers,
                         weight_hipo, idx, node)

            if constr in ['aae', 'aa']:
                self.aae(hiper_pl, hiper_en, weight_hiper, avg_weight, idx,
                         node)

            if constr in ['aao', 'aa']:
                self.aao(hipo_pl, hipo_en, avg_weight, weight_hipo,
                         hipo_pl_layers,
                         hipo_en_layers,
                         idx, node)

            if constr in ['aab', 'aa']:
                self.aab(hiper_pl, hiper_en, hipo_en, hipo_pl,
                         hipo_pl_layers,
                         hipo_en_layers, idx, node)

    # operated
    def iie(self, father_pl, father_en, node, idx, weight_hipernym, average_weight):
        """Fathers and fathers."""
        if self.mapped.get(father_pl) == father_en:
            weight_val = weight_hipernym * average_weight
            node.add_weight(idx, weight_val)

    # operated
    def iio(self, children_pl, sons, idx, node, weight_hiponym, average_weight):
        """Sons and sons."""
        for son in children_pl:
            if self.mapped.get(son) in sons:
                weight_val = weight_hiponym * average_weight
                node.add_weight(idx, weight_val)

    # operated
    def iib(self, father_pl, father_en, children_pl, sons, idx, node):
        """Sons and fathers on both."""
        if not (self.mapped.get(father_pl) == father_en):
            return
        for son in children_pl:
            if self.mapped.get(son) in sons:
                # 10 > 6 = average candidate length (look article)
                weight_val = 10 / (len(node.weights) ** 2)
                node.add_weight(idx, weight_val)

    def aie(self, father_en, hipernyms_pl, avg_weight, weight_hiper, idx, node):
        """Ancestor and father."""
        for ancestor in hipernyms_pl:
            if ancestor in self.mapped and self.mapped[ancestor] == father_en:
                distance = (hipernyms_pl.index(ancestor))
                weight_val = weight_hiper * avg_weight / (2 ** distance)
                node.add_weight(idx, weight_val)

    def aio(self, hiponyms_pl, hipo_pl_layers, sons, avg_weight, weight_hipo, idx, node):
        """Descendant and child."""
        for descendant in hiponyms_pl:
            if descendant in self.mapped and self.mapped[descendant] in sons:
                distance = [descendant in p for p in hipo_pl_layers].index(True)
                weight_val = weight_hipo * avg_weight / (2 ** distance)
                node.add_weight(idx, weight_val)

    def aib(self, hipernyms_pl, father_en, hipo_pl, hipo_pl_layers, sons, idx, node):
        """Ancestors/Descendent and father/son."""
        any_ = False
        dist_anc = 0
        for ancestor in hipernyms_pl:
            if ancestor in self.mapped and self.mapped[ancestor] == father_en:
                any_ = True
                dist_anc = hipernyms_pl.index(ancestor)
        if not any_:
            return
        for descendant in hipo_pl:
            if descendant in self.mapped and self.mapped[descendant] in sons:
                dist_desc = [descendant in p for p in hipo_pl_layers].index(True)
                weight_val = (15 / len(node.weights) ** 2) / (2 ** max(dist_anc, dist_desc))
                node.add_weight(idx, weight_val)

    def iae(self, father_pl, hipernyms_en, weight_hiper, avg_weight, idx, node):
        """Father and ancestor."""
        if father_pl in self.mapped and self.mapped[father_pl] in hipernyms_en:
            distance = hipernyms_en.index(self.mapped[father_pl])
            weight_val = weight_hiper * avg_weight / (2 ** distance)
            node.add_weight(idx, weight_val)

    def iao(self, children_pl, hiponyms_en, weight_hipo, avg_weight, hipo_en_layers, idx, node):
        """Sons and descendent"""
        for syn in children_pl:
            if syn in self.mapped and self.mapped[syn] in hiponyms_en:
                distance = [self.mapped[syn] in q for q in hipo_en_layers].index(True)
                weight_val = weight_hipo * avg_weight / (2 ** distance)
                node.add_weight(idx, weight_val)

    def iab(self, father_pl, hipernyms_en, children_pl, hiponyms_en, weight_hiper, hipo_en_layers,
            weight_hipo, idx, node):
        """Father and ancestor + Son and descendent."""
        if not (father_pl in self.mapped and self.mapped[father_pl] in hipernyms_en):
            return
        weight_hiper = weight_hiper / (2 ** (hipernyms_en.index(self.mapped[father_pl])))
        for syn in children_pl:
            if syn in self.mapped and self.mapped[syn] in hiponyms_en:
                dist = ([self.mapped[syn] in q for q in hipo_en_layers].index(True))
                weight_val = 2. * weight_hiper + weight_hipo / (2. ** dist)
                node.add_weight(idx, weight_val)

    def aae(self, hipernyms_pl, hipernyms_en, weight_hiper, avg_weight, idx, node):
        """Ancestor and ancestor."""
        for hipernym in hipernyms_pl:
            if hipernym in self.mapped and self.mapped[hipernym] in hipernyms_en:
                weight_val = weight_hiper * avg_weight / (
                    2 ** max(hipernyms_pl.index(hipernym),
                             hipernyms_en.index(self.mapped[hipernym])))
                node.add_weight(idx, weight_val)

    def aao(self, hipo_pl, hiponyms_en, avg_weight, weight_hipo, hipo_pl_layers, hipo_en_layers,
            idx, node):
        """Descendent and descendent."""
        for hipo in hipo_pl:
            if hipo in self.mapped and self.mapped[hipo] in hiponyms_en:
                weight_val = weight_hipo * avg_weight / (
                    2 ** max([hipo in p for p in hipo_pl_layers].index(True),
                             [self.mapped[hipo] in q for q in hipo_en_layers].index(True)))
                node.add_weight(idx, weight_val)

    def aab(self, hipernyms_pl, hipernyms_en, hiponyms_en, hipo_pl, hipo_pl_layers,
            hipo_en_layers, idx, node):
        """Descendents and ancestors"""
        any_ = False
        dist_pl = dist_en = 0
        for hiper in hipernyms_pl:
            if hiper in self.mapped and self.mapped[hiper] in hipernyms_en:
                any_ = True
                dist_pl = hipernyms_pl.index(hiper)
                dist_en = hipernyms_en.index(self.mapped[hiper])
        if not any_:
            return
        for hipo in hipo_pl:
            if hipo in self.mapped and self.mapped[hipo] in hiponyms_en:
                weight_val = (2 ** (
                    [hipo in p for p in hipo_pl_layers].index(True) +
                    [self.mapped[hipo] in q for q in hipo_en_layers]
                    .index(True) + dist_pl + dist_en))
                # 10 > 6 = srednia liczba kandydatow (patrz artykul)
                weight_val = (20. / (len(node.weights) ** 2)) / weight_val
                node.add_weight(idx, weight_val)
