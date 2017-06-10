# -*- coding: utf-8 -*-


def hiper(synset):
    """Count hipernyms for the synset.

    Parameters
    ----------
    synset : pyrelaxmapper.rlabel.rlsource.RLSynset
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


def hipo(synset):
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
    children = hipo_layers[0]
    return hiponyms, hipo_layers, children


def hiper_path(synset):
    """Find hipernyms for PWN synset.

    Parameters
    ----------
    synset : pyrelaxmapper.rlabel.rlsource.RLSynset
        Synset
    """
    parent = []
    hipernyms = []
    hipernym_paths = synset.hypernym_paths()

    # TODO: Currently algorithm only takes into account clear paths!!
    if len(hipernym_paths) == 1:
        hipernyms = [hipernym.id_() for hipernym in hipernym_paths[0]]
        # element 0 is our synset, so we skip it.
        # direction: from synset rather than to synset.
        hipernyms = hipernyms[1::-1]

        parent = hipernyms[0]
    return hipernyms, parent
