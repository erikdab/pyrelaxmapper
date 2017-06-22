# -*- coding: utf-8 -*-
"""plWordNet DB queries."""
from sqlalchemy import orm
from sqlalchemy.sql import func, expression

from . import models
from .models import LexicalUnit, Synset, SynsetRelation, RelationType, UnitSynset, LexicalRelation


def version(session):
    """Query plWordNet for format version."""
    return session.query(models.Parameter).filter_by(name='programversion').first().value


def reltypes(session, types=None):
    """Query for hipernyms.

    Parameters
    ----------
    session : orm.session.Session
    types : list
        RelationType to select (default [10, 11], hiper/hiponyms)
    """
    return (session.query(RelationType)
            )


def reltypes_pwn_plwn(session):
    """Query plWN for PWN-plWN relation types."""
    return (session.query(RelationType.id_)
            .filter(RelationType.name.like('%plWN%'))
            # Don't take potential, only take certain candidates
            .filter(~ RelationType.shortcut.in_(['po_pa', 'po_ap'])))


# Use unified id ('n')
def pwn_mappings(session, pos=None):
    """Query plWN for already mapped synsets between plWN and PWN.

    Selects: polish synset id, english synset unitsstr, POS
    Source: Polish  -  Target (child): English
    RelationType: selects only plWN-PWN mappings
        does not take 'po_pa, po_ap' relation types.
    POS: Only selects nouns

    Parameters
    ----------
    session : orm.session.Session
    pos : list of str
    """
    # pos_dict = files.pos()
    # pos_en = []
    if not pos:
        pos = ['n']
    # for pos_ in pos:
    #     pos_en
    rel_types = reltypes_pwn_plwn(session)

    syns_en = orm.aliased(Synset)
    uas_pl = orm.aliased(UnitSynset)
    lunit_pl = orm.aliased(LexicalUnit)
    # return (session.query(Synset.id_, syns_en.unitsstr, LexicalUnit.pos)
    return (session.query(Synset.id_)
            .join(SynsetRelation, Synset.id_ == SynsetRelation.parent_id)
            .join(syns_en, SynsetRelation.child_id == syns_en.id_)

            .join(UnitSynset, syns_en.id_ == UnitSynset.syn_id)
            .join(LexicalUnit, UnitSynset.lex_id == LexicalUnit.id_)

            .join(uas_pl, Synset.id_ == uas_pl.syn_id)
            .join(lunit_pl, uas_pl.lex_id == lunit_pl.id_)

            .join(RelationType, SynsetRelation.rel_id == RelationType.id_)
            .filter(RelationType.id_.in_(rel_types))
            .filter(LexicalUnit.pos.in_(['6']))
            .filter(lunit_pl.pos.in_(['2']))

            .group_by(Synset.id_)
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
                          expression.label('lex_ids', func.group_concat(UnitSynset.lex_id)),
                          expression.label('unitindexes', func.group_concat(UnitSynset.unitindex))
                          )
            .join(UnitSynset)
            .join(LexicalUnit)
            .filter(LexicalUnit.pos.in_(pos))
            .order_by(Synset.id_)
            .group_by(Synset.id_)
            )


def synset_relations(session, types, pos=None):
    """Query for hipernyms.

    Parameters
    ----------
    session : orm.session.Session
    types : list
        RelationType to select (default [10, 11], hiper/hiponyms)
    """
    query = (session.query(SynsetRelation.parent_id, SynsetRelation.child_id,
                           SynsetRelation.rel_id)
             .order_by(SynsetRelation.parent_id)
             )
    if types:
        types = types if isinstance(types, list) else [types]
        query = query.filter(SynsetRelation.rel_id.in_(types))
    if pos:
        pos = pos if isinstance(pos, list) else [pos]
        query = (query
                 .join(UnitSynset, SynsetRelation.parent_id == UnitSynset.syn_id)
                 .join(LexicalUnit)
                 .filter(LexicalUnit.pos.in_(pos))
                 .group_by(SynsetRelation.parent_id, SynsetRelation.child_id,
                           SynsetRelation.rel_id)
                 )

    return query


def lexical_relations(session, rel_types, pos=None):
    """Query for hipernyms.

    Parameters
    ----------
    session : orm.session.Session
    rel_types : list
        RelationType to select
    pos : list
        Parts of speech to extract. If empty, extract all.
    """
    query = (session.query(LexicalRelation.parent_id, LexicalRelation.child_id,
                           LexicalRelation.rel_id)
             .order_by(LexicalRelation.parent_id)
             )
    if rel_types:
        rel_types = rel_types if isinstance(rel_types, list) else [rel_types]
        query = query.filter(LexicalRelation.rel_id.in_(rel_types))
    if pos:
        pos = pos if isinstance(pos, list) else [pos]
        query = (query
                 .join(LexicalUnit, LexicalRelation.parent_id == LexicalUnit.id_)
                 .filter(LexicalUnit.pos.in_(pos))
                 .group_by(LexicalRelation.parent_id, LexicalRelation.child_id)
                 )
    return query