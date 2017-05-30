# -*- coding: utf-8 -*-

"""Data utilities."""

import os
import logging

logger = logging.getLogger()


def cascade_dicts(directory):
    """Creates a cascading dictionary from bilingual sources

    Parameters
    ----------
    directory : string
        Directory containing dictionaries to cascade together.

        Structure:
          listing.txt         # Ordered list of dictionaries in 'dicts'
          dicts/*/dict.txt    # Dictionary file with translations

        'listing.txt' format: comma-separated ordered list, example:
            "dicts_dir1,dicts_dir3,dicts_dir2"
        'dict.txt'    format: tab-delimited translations, example:
            "term1 \t translation1
             term2 \t translation2"

    Returns
    -------
    dict
        The created dictionary if successful, empty dict otherwise"""
    lang_dict = {}
    listing = _read_listing(directory)
    files = [os.path.join(directory, 'dicts', f, 'dict.txt') for f in listing]

    for line in _fileinput(files):
        term, translation = _parse_translation(line)
        if term and translation:
            lang_dict.setdefault(term, []).append(translation)

    return lang_dict


# Could load cfg or json
def _read_listing(directory):
    """Reads the dictionary listing."""
    listing_file = os.path.join(directory, 'listing.txt')
    if not os.path.exists(listing_file):
        logger.error('Dictionary listing is missing. Check path: {0}. '.format(directory))
        return []

    with open(listing_file, 'r') as content_file:
        listing = content_file.read().strip().split(',')
    return listing


def _fileinput(files):
    """Yield all lines in a list of files."""
    for f in files:
        if not os.path.exists(f):
            logger.debug('File {0} does not exist.'.format(f))
            continue
        with open(f, 'r') as fin:
            for line in fin:
                yield line


def _parse_translation(line):
    """Parse line to extract term and translation"""
    cols = [col.strip().replace(' ', '_') for col in line.split('\t')]
    if len(cols) != 2:
        logger.debug('Wrong format in line: {0}\n'.format(line))
        cols = [None] * 2
    return cols
