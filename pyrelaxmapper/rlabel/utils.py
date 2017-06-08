# -*- coding: utf-8 -*-


def hiper(synset, hiper_func):
    """Count hipernyms for the synset.

    Parameters
    ----------
    synset
        Synset name / id
    hiper_func
        A function returning direct hipernyms for synset.
    """
    do_now = [synset]
    hipernyms = []
    while do_now:
        do_next = []
        for node in do_now:
            do_next.extend(hiper_func(node))
        do_now = do_next
        hipernyms.extend(do_next)
    parent = hipernyms[0] if hipernyms else 0
    return hipernyms, parent


def hiper2(synset):
    """Count hipernyms for the synset.

    Parameters
    ----------
    synset : pyrelaxmapper.rlabel.wordnet.RLSynset
        Synset
    """
    do_now = [synset]
    hipernyms = []
    while do_now:
        do_next = []
        for node in do_now:
            do_next.extend(node.hypernyms())
        do_now = do_next
        hipernyms.extend(do_next)
    parent = hipernyms[0] if hipernyms else 0
    return hipernyms, parent


def hipo(synset, hipo_func):
    """Find hiponyms for synset.

    Parameters
    ----------
    synset
        Synset name (text)
    hipo_func : FunctionType
        A function returning direct hyponims for synset.
        Can be a partial.
    """
    todo = [synset]
    hiponyms = []
    hipo_layers = []
    while todo:
        do_next = []
        for node in todo:
            do_next.extend(hipo_func(node))
        todo = do_next
        hiponyms.extend(todo)
        if todo:
            hipo_layers.append(todo)
    children = hipo_layers[0]
    return hiponyms, hipo_layers, children


def hipo2(synset):
    """Find hiponyms for synset.

    Parameters
    ----------
    synset : pyrelaxmapper.rlabel.wordnet.RLSynset
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
    children = hipo_layers[0]
    return hiponyms, hipo_layers, children
