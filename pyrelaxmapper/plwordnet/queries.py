# -*- coding: utf-8 -*-
"""plWordNet DB queries."""
from sqlalchemy import orm
from sqlalchemy.sql import func, expression

import conf
from . import models
from .models import LexicalUnit, Synset, SynsetRelation, RelationType, UnitSynset


def version(session):
    """Query plWordNet for format version."""
    return session.query(models.Parameter).filter_by(name='programversion').first().value


def relationtypes(session, types=None):
    """Query for hipernyms.

    Parameters
    ----------
    session : orm.session.Session
    types : list
        RelationType to select (default [10, 11], hiper/hiponyms)
    """
    return (session.query(RelationType)
            )


def relationtypes_pwn_plwn(session):
    """Query plWN for PWN-plWN relation types."""
    return (session.query(RelationType.id_)
            .filter(RelationType.name.like('%plWN%'))
            # Don't take potential, only take certain candidates
            .filter(~ RelationType.shortcut.in_(['po_pa', 'po_ap'])))


def pwn_mappings(session):
    """Query plWN for already mapped synsets between plWN and PWN.

    Selects: polish synset id, english synset unitsstr, POS
    Source: Polish  -  Target (child): English
    RelationType: selects only plWN-PWN mappings
        does not take 'po_pa, po_ap' relation types.
    POS: Only selects nouns

    Parameters
    ----------
    session : orm.session.Session
    """
    rel_types = relationtypes_pwn_plwn(session)

    syns_en = orm.aliased(Synset)
    return (session.query(Synset.id_, syns_en.unitsstr, LexicalUnit.pos)
            .join(SynsetRelation, Synset.id_ == SynsetRelation.parent_id)
            .join(syns_en, SynsetRelation.child_id == syns_en.id_)

            .join(UnitSynset, syns_en.id_ == UnitSynset.syn_id)
            .join(LexicalUnit, UnitSynset.lex_id == LexicalUnit.id_)

            .join(RelationType, SynsetRelation.rel_id == RelationType.id_)
            .filter(RelationType.id_.in_(rel_types))
            .filter(LexicalUnit.pos > 4)
            # Before wasn't grouped!
            .group_by(Synset.id_, syns_en.unitsstr, LexicalUnit.pos)
            .order_by(Synset.id_)
            )


def lunits(session, pos=None):
    """Query for lexical units, their lemma and POS.

    Parameters
    ----------
    session : orm.session.Session
    pos : list
        Parts of speech to select (default [2])

    Returns
    -------

    """
    if not pos:
        pos = [2]
    return (session.query(LexicalUnit.id_, LexicalUnit.lemma, LexicalUnit.pos)
            .filter(LexicalUnit.pos.in_(pos))
            .order_by(LexicalUnit.id_)
            )


def synsets(session, pos=None):
    """Query for synsets, concatenated ids and lemmas of their LUs.

    Parameters
    ----------
    session : orm.session.Session
    pos : list
        Parts of speech to select (default [2])
    """
    if not pos:
        pos = [2]
    return (session.query(Synset.id_,
                          expression.label('lu_ids', func.group_concat(LexicalUnit.id_)),
                          expression.label('lu_lemmas', func.group_concat(LexicalUnit.lemma))
                          )
            .join(UnitSynset)
            .join(LexicalUnit)
            .filter(LexicalUnit.pos.in_(pos))
            .order_by(Synset.id_)
            .group_by(Synset.id_)
            )


def synsets2(session, pos=None):
    """Query for synsets, concatenated ids and lemmas of their LUs.

    Parameters
    ----------
    session : orm.session.Session
    pos : list
        Parts of speech to select (default [2])
    """
    if not pos:
        pos = [2]
    return (session.query(Synset.id_,
                          expression.label('lex_ids', func.group_concat(UnitSynset.lex_id)),
                          expression.label('unitindexes', func.group_concat(UnitSynset.unitindex))
                          )
            .join(UnitSynset)
            .join(LexicalUnit)
            .filter(LexicalUnit.pos.in_(pos))
            .order_by(Synset.id_)
            .group_by(Synset.id_)
            )


def synset_relations2(session, type, pos=None):
    """Query for hipernyms.

    Parameters
    ----------
    session : orm.session.Session
    types : list
        RelationType to select (default [10, 11], hiper/hiponyms)
    """
    if not pos:
        pos = [2]
    return (session.query(SynsetRelation.parent_id, SynsetRelation.child_id)
            .join(UnitSynset, SynsetRelation.parent_id == UnitSynset.syn_id)
            .join(LexicalUnit)
            .filter(SynsetRelation.rel_id == type)
            .filter(LexicalUnit.pos.in_(pos))
            .order_by(SynsetRelation.parent_id)
            .group_by(SynsetRelation.parent_id, SynsetRelation.child_id)
            )


def synset_relations(session, types=None):
    """Query for hipernyms.

    Parameters
    ----------
    session : orm.session.Session
    types : list
        RelationType to select (default [10, 11], hiper/hiponyms)
    """
    if types is None:
        types = [10, 11]
    return (session.query(SynsetRelation.parent_id, SynsetRelation.child_id)
            .filter(SynsetRelation.rel_id.in_(types))
            .order_by(SynsetRelation.rel_id, SynsetRelation.parent_id)
            )


def extract_files(session, nouns_only=True):
    """Extract data from plWordNet to files."""
    with open(conf.results('units.txt'), "w", encoding="utf-8") as file:
        lunits_ = lunits(session).all()
        file.write('\n'.join('{} {}'.format(lunit.id_, lunit.name.replace(' ', '_'))
                             for lunit in lunits_))

    with open(conf.results('synsets.txt'), "w", encoding="utf-8") as file_ids, \
            open(conf.results('synsets_text.txt'), "w", encoding="utf-8") as file_text:
        synsets_ = synsets(session).all()

        lu_ids = ('{} {}'.format(synset.id_, ' '.join(synset.lu_ids.split(',')))
                  for synset in synsets_)
        file_ids.write('\n'.join(lu_ids))

        lu_lemmas = ('{} {}'.format(synset.id_,
                                    ' '.join(synset.lu_lemmas.replace(' ', '_').split(',')))
                     for synset in synsets_)
        file_text.write('\n'.join(lu_lemmas))

    with open(conf.results('synset_hipernyms.txt'), "w", encoding="utf-8") as file_hiper, \
            open(conf.results('synset_hiponyms.txt'), "w", encoding="utf-8") as file_hipo:
        hiper_count = synset_relations(session, [10]).count()
        relations = synset_relations(session).all()
        hipernyms, hiponyms = relations[:hiper_count], relations[hiper_count:]

        hipernyms_out = ('{} {}'.format(relation.parent_id, relation.child_id)
                         for relation in hipernyms)
        file_hiper.write('\n'.join(hipernyms_out))

        hiponyms_out = ('{} {}'.format(relation.parent_id, relation.child_id)
                        for relation in hiponyms)
        file_hipo.write('\n'.join(hiponyms_out))
