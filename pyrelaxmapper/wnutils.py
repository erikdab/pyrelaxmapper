# -*- coding: utf-8 -*-
import logging
import os
import pickle
import re

from pyrelaxmapper import conf

logger = logging.getLogger()


# Could be placed inside rlsource!
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


def cached(name, func, args=None, info=None, group=None):
    """Load from cache file or create and save to cached file.

    Parameters
    ----------
    name
        Name of cache file
    func
        Can be function, or class
    args
        Args to pass to function / class
    info
        Info to print.
    """
    if args is None:
        args = []
    elif not isinstance(args, list):
        args = [args]

    filename = conf.cache(name if not group else os.path.join(group, name))

    if '.pkl' not in filename:
        filename += '.pkl'

    group_name = '{}/{}'.format(group, name) if group else name
    source = 'from cache' if os.path.exists(filename) else 'live'
    logger.info('Loading "{}" {}.'.format(group_name, source))

    data = None
    if source == 'from cache':
        try:
            data = load_obj(filename)
        except ModuleNotFoundError as e:
            logger.debug('Cache loading error "{}". File: {}.'.format(e, filename))
    if not data:
        data = func(*args)
        save_obj(data, filename)

    # Also: Object generation function may have their own caches!
    # WHY? For time measurement. We know exactly how long it took!
    logger.info('Loaded "{}".'.format(group_name))
    return data


def save_obj(obj, name):
    with open(name, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name, 'rb') as f:
        return pickle.load(f)


# Should handle terms which are ONLY Symbols!
def clean(term, spaces=False):
    rep = {'(': '', ')': '', 'the ': '', '/': '', ' ': '_', '-': '_', ',': ''}
    # if spaces:
    #     rep[' '] = '_'
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
