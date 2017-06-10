# -*- coding: utf-8 -*-


class Relaxer:
    """Relaxation labeling relaxer."""
    _constraints = None


class Constraint2:
    """A constraint to be used in Relaxation Labeling."""
    def __init__(self, status, weight):
        self._status = status
        self._weight = weight

    def apply(self):
        """Apply constraint."""
        pass


class Constraint:

    def id(self):
        pass

    def name(self):
        pass

    def apply(self):
        """Apply to node."""
        pass

    def requires(self):
        pass


def _add_weight(weights, idx_add, amount):
    """Add to one weight, while decreasing others to keep balance."""
    sub = amount / (len(weights) - 1)
    for idx in range(len(weights)):
        weights[idx] += amount if idx == idx_add else -sub


def iie(mapped, father_pl, father_en, weights, idx, weight_hipernym, average_weight):
    """Fathers and fathers."""
    if father_pl in mapped and mapped[father_pl] == father_en:
        weight_val = weight_hipernym * average_weight
        _add_weight(weights, idx, weight_val)


def iio(mapped, children_pl, sons, idx, weights, weight_hiponym, average_weight):
    """Sons and sons."""
    for son in children_pl:
        if son in mapped and mapped[son] in sons:
            weight_val = weight_hiponym * average_weight
            _add_weight(weights, idx, weight_val)


def iib(mapped, father_pl, father_en, children_pl, sons, idx, weights):
    """Sons and fathers on both."""
    if not (father_pl in mapped and mapped[father_pl] == father_en):
        return
    for syn in children_pl:
        if syn in mapped and mapped[syn] in sons:
            # 10 > 6 = average candidate length (look article)
            weight_val = 10. / (len(weights) * len(weights))
            _add_weight(weights, idx, weight_val)


def aie(mapped, father_en, hipernyms_pl, avg_weight, weight_hiper, idx, weights):
    """Ancestor and father."""
    for ancestor in hipernyms_pl:
        if ancestor in mapped and mapped[ancestor] == father_en:
            distance = (hipernyms_pl.index(ancestor))
            weight_val = weight_hiper * avg_weight / (2 ** distance)
            _add_weight(weights, idx, weight_val)


def aio(mapped, hiponyms_pl, hipo_pl_layers, sons, avg_weight, weight_hipo, idx, weights):
    """Descendant and child."""
    for descendant in hiponyms_pl:
        if descendant in mapped and mapped[descendant] in sons:
            distance = [descendant in p for p in hipo_pl_layers].index(True)
            weight_val = weight_hipo * avg_weight / (2 ** distance)
            _add_weight(weights, idx, weight_val)


def aib(mapped, hipernyms_pl, father_en, hipo_pl, hipo_pl_layers, sons, idx, weights):
    """Ancestors/Descendent and father/son."""
    any_ = False
    dist_anc = 0
    for ancestor in hipernyms_pl:
        if ancestor in mapped and mapped[ancestor] == father_en:
            any_ = True
            dist_anc = hipernyms_pl.index(ancestor)
    if not any_:
        return
    for descendant in hipo_pl:
        if descendant in mapped and mapped[descendant] in sons:
            dist_desc = [descendant in p for p in hipo_pl_layers].index(True)
            weight_val = (15 / len(weights) ** 2) / (2 ** max(dist_anc, dist_desc))
            _add_weight(weights, idx, weight_val)


def iae(mapped, father_pl, hipernyms_en, weight_hiper, avg_weight, idx, weights):
    """Father and ancestor."""
    if father_pl in mapped and mapped[father_pl] in hipernyms_en:
        distance = hipernyms_en.index(mapped[father_pl])
        weight_val = weight_hiper * avg_weight / (2 ** distance)
        _add_weight(weights, idx, weight_val)


def iao(mapped, children_pl, hiponyms_en, weight_hipo, avg_weight, hipo_en_layers, idx, weights):
    """Sons and descendent"""
    for syn in children_pl:
        if syn in mapped and mapped[syn] in hiponyms_en:
            distance = [mapped[syn] in q for q in hipo_en_layers].index(True)
            weight_val = weight_hipo * avg_weight / (2 ** distance)
            _add_weight(weights, idx, weight_val)


def iab(mapped, father_pl, hipernyms_en, children_pl, hiponyms_en, weight_hiper, hipo_en_layers,
        weight_hipo, idx, weights):
    """Father and ancestor + Son and descendent."""
    if not (father_pl in mapped and mapped[father_pl] in hipernyms_en):
        return
    weight_hiper = weight_hiper / (2 ** (hipernyms_en.index(mapped[father_pl])))
    for syn in children_pl:
        if syn in mapped and mapped[syn] in hiponyms_en:
            dist = ([mapped[syn] in q for q in hipo_en_layers].index(True))
            weight_val = 2. * weight_hiper + weight_hipo / (2. ** dist)
            _add_weight(weights, idx, weight_val)


def aae(mapped, hipernyms_pl, hipernyms_en, weight_hiper, avg_weight, idx, weights):
    """Ancestor and ancestor."""
    for hipernym in hipernyms_pl:
        if hipernym in mapped and mapped[hipernym] in hipernyms_en:
            weight_val = weight_hiper * avg_weight / (
                2 ** max(hipernyms_pl.index(hipernym),
                         hipernyms_en.index(mapped[hipernym])))
            _add_weight(weights, idx, weight_val)


def aao(mapped, hipo_pl, hiponyms_en, avg_weight, weight_hipo, hipo_pl_layers, hipo_en_layers,
        idx, weights):
    """Descendent and descendent."""
    for hipo in hipo_pl:
        if hipo in mapped and mapped[hipo] in hiponyms_en:
            weight_val = weight_hipo * avg_weight / (
                2 ** max([hipo in p for p in hipo_pl_layers].index(True),
                         [mapped[hipo] in q for q in hipo_en_layers].index(True)))
            _add_weight(weights, idx, weight_val)


def aab(mapped, hipernyms_pl, hipernyms_en, hiponyms_en, hipo_pl, hipo_pl_layers,
        hipo_en_layers, idx, weights):
    """Descendents and ancestors"""
    any_ = False
    dist_pl = dist_en = 0
    for hiper in hipernyms_pl:
        if hiper in mapped and mapped[hiper] in hipernyms_en:
            any_ = True
            dist_pl = hipernyms_pl.index(hiper)
            dist_en = hipernyms_en.index(mapped[hiper])
    if not any_:
        return
    for hipo in hipo_pl:
        if hipo in mapped and mapped[hipo] in hiponyms_en:
            weight_val = (2 ** (
                [hipo in p for p in hipo_pl_layers].index(True) +
                [mapped[hipo] in q for q in hipo_en_layers]
                .index(True) + dist_pl + dist_en))
            # 10 > 6 = srednia liczba kandydatow (patrz artykul)
            weight_val = (20. / (len(weights) ** 2)) / weight_val
            _add_weight(weights, idx, weight_val)
