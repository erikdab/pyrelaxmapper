# -*- coding: utf-8 -*-
"""Data management utilities."""
import logging

from pyrelaxmapper import utils

logger = logging.getLogger()


def cascade_dicts(lines):
    """Creates a cascading dictionary from source-target sources

    Parameters
    ----------
    lines : list
        Lines with translations to cascade together into a single dict.

    Returns
    -------
    dict
        Cascaded single dict."""
    lang_dict = {}
    for line in lines:
        term, translation = _parse_translation(line)
        if term and translation and translation not in lang_dict.get(term, []):
            lang_dict.setdefault(term, []).append(translation)

    return lang_dict


# TODO: Consider improving this.
def _parse_translation(line):
    """Parse tab-delimited line to extract term and translation."""
    rep = {' ': '_', '(': '', ')': '', 'the ': ''}
    cols = [utils.multi_replace(col.strip().lower(), rep) for col in line.split('\t')]
    if len(cols) != 2:
        logger.debug('Wrong format in line: {0}\n'.format(line))
        cols = [None] * 2
    return cols
