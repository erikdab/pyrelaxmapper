# -*- coding: utf-8 -*-
import logging
import os
import pickle
import re

import conf

logger = logging.getLogger()


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

    loaded = False
    if os.path.exists(filename):
        logger.info('Loading {} from cache.'.format(func.__name__, filename))
        try:
            source = load_obj(filename)
            loaded = True
        except ModuleNotFoundError as e:
            logger.debug('Cache loading error "{}". File: {}.'.format(e, filename))
    if not loaded:
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


def clean(term, spaces=False):
    rep = {'(': '', ')': '', 'the ': '', '/': ''}
    if spaces:
        rep[' '] = '_'
    return multi_replace(term.strip().lower(), rep).strip()


def multi_replace(text, replacements, ignore_case=False):
    """
    Given a string and a dict, replaces occurrences of the dict keys found in the
    string, with their corresponding values. The replacements will occur in "one pass",
    i.e. there should be no clashes.

    Parameters
    ----------
    text : str
        string to perform replacements on
    replacements : dict
        replacement dictionary {str_to_find: str_to_replace_with}
    ignore_case : bool
        whether to ignore case when looking for matches

    Returns
    -------
    str
        str the replaced string
    """
    # Sort by length so that the shorter strings don't replace the longer ones.
    rep_sorted = sorted(replacements, key=lambda s: len(s[0]), reverse=True)

    rep_escaped = [re.escape(replacement) for replacement in rep_sorted]

    pattern = re.compile("|".join(rep_escaped), re.I if ignore_case else 0)

    return pattern.sub(lambda match: replacements[match.group(0)], text)
