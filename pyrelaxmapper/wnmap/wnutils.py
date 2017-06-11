# -*- coding: utf-8 -*-
import os
import logging
import pickle

from nltk.corpus import wordnet as pwn

import conf

logger = logging.getLogger()


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
    children = hipo_layers[0] if hipo_layers else []
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
        hipernyms = [hipernym for hipernym in hipernym_paths[0]]
        # element 0 is our synset, so we skip it.
        # direction: from synset rather than to synset.
        hipernyms = hipernyms[1::][::-1]

        parent = hipernyms[0]
    return hipernyms, parent


def _hip_pl(node, hip):
    """Direct hiponyms/hipernyms for plWN node."""
    return [node_hip for node_hip in hip[node]] if node in hip else []


def _hipo_en(node):
    """Direct hiponyms for PWN node:"""
    return [hypo_node.name() for hypo_node in pwn.synset(node).hyponyms()]


def _hiper_en(synset):
    """Find hipernyms for PWN synset."""
    parent = []
    hipernyms = pwn.synset(synset).hypernym_paths()

    # TODO: For now only clear paths are used.
    if len(hipernyms) == 1:
        # Proper direction (synset -> hiper -> hiper of hiper). Don't take synset.
        hipernyms = [hiper.name() for hiper in hipernyms[0]][1::-1]
        parent = hipernyms[0]
    return hipernyms, parent


def cached(filename, func, args=None, info=None):
    """Load from cache file or create and save to cached file.

    Parameters
    ----------
    filename
        file to load/save cache
    func
        Can be function, or class
    args
        Args to pass to function / class
    info
        Info to print.
    """
    if args is None:
        args = []

    if not isinstance(args, list):
        args = [args]

    if '.pkl' not in filename:
        filename += '.pkl'

    filename = conf.cache(filename)

    if os.path.exists(filename):
        logger.info('Loading {} from cache.'.format(func.__name__))
        source = load_obj(filename)
    else:
        logger.info('Loading {} live.'.format(func.__name__))
        source = func(*args)
        save_obj(source, filename)
    logger.info('Loaded {}.'.format(func.__name__))
    return source


def save_obj(obj, name):
    with open(name, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name, 'rb') as f:
        return pickle.load(f)
