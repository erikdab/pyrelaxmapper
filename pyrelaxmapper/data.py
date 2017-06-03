# -*- coding: utf-8 -*-
"""Data management utilities."""
import logging

from pyrelaxmapper import utils, conf
from pyrelaxmapper.plwordnet import queries as plqueries

logger = logging.getLogger()


# TODO: Combine this and XML dict loading (Receive term and translations by generator)
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
        term, translation = _clean_translation(line)
        if term and translation and translation not in lang_dict.get(term, []):
            lang_dict.setdefault(term, []).append(translation)

    return lang_dict


# TODO: Consider improving this.
def _clean_translation(line):
    """Parse tab-delimited line to extract term and translation."""
    rep = {' ': '_', '(': '', ')': '', 'the ': '', '/': ''}
    cols = [utils.multi_replace(col.strip().lower(), rep) for col in line.split('\t')]
    if len(cols) != 2:
        logger.debug('Wrong format in line: {0}\n'.format(line))
        cols = [None] * 2
    return cols


def db_extract(session, nouns_only=True):
    """Extract data from plWordNet to files."""
    with open(conf.results('units.txt'), "w", encoding="utf-8") as file:
        lunits = plqueries.lunits(session).all()
        file.write('\n'.join('{} {}'.format(lunit.id_, lunit.lemma.replace(' ', '_'))
                             for lunit in lunits))

    with open(conf.results('synsets.txt'), "w", encoding="utf-8") as file_ids, \
            open(conf.results('synsets_text.txt'), "w", encoding="utf-8") as file_text:
        synsets = plqueries.synsets(session).all()

        lu_ids = ('{} {}'.format(synset.id_, ' '.join(synset.lu_ids.split(',')))
                  for synset in synsets)
        file_ids.write('\n'.join(lu_ids))

        lu_lemmas = ('{} {}'.format(synset.id_,
                                    ' '.join(synset.lu_lemmas.replace(' ', '_').split(',')))
                     for synset in synsets)
        file_text.write('\n'.join(lu_lemmas))

    with open(conf.results('synset_hiperonimia.txt'), "w", encoding="utf-8") as file_hiper, \
            open(conf.results('synset_hiponimia.txt'), "w", encoding="utf-8") as file_hipo:
        hiper_count = plqueries.synset_relations(session, [10]).count()
        relations = plqueries.synset_relations(session).all()
        hipernymy, hiponymy = relations[:hiper_count], relations[hiper_count:]

        hipernymy_out = ('{} {}'.format(relation.parent_id, relation.child_id)
                         for relation in hipernymy)
        file_hiper.write('\n'.join(hipernymy_out))

        hiponymy_out = ('{} {}'.format(relation.parent_id, relation.child_id)
                        for relation in hiponymy)
        file_hipo.write('\n'.join(hiponymy_out))
