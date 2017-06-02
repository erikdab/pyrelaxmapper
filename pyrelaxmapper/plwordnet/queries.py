# -*- coding: utf-8 -*-
"""plWordNet DB queries."""
from .models import LexicalUnit, Synset, SynsetRelation, RelationType, UnitSynset
from . import models
from sqlalchemy import orm


def version(session):
    """Query plWordNet for format version."""
    return session.query(models.Parameter).filter_by(name='programversion').first().value


def relationtypes_pwn_plwn(session):
    """Query plWN for PWN-plWN relation types."""
    return (session.query(RelationType.id_)
            .filter(RelationType.name.like('%plWN%'))
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
    mappings = (session.query(Synset.id_, syns_en.unitsstr, LexicalUnit.pos)
                .join(SynsetRelation, Synset.id_ == SynsetRelation.parent_id)
                .join(syns_en, SynsetRelation.child_id == syns_en.id_)

                .join(UnitSynset, syns_en.id_ == UnitSynset.syn_id)
                .join(LexicalUnit, UnitSynset.lex_id == LexicalUnit.id_)

                .join(RelationType, SynsetRelation.rel_id == RelationType.id_)
                .filter(RelationType.id_.in_(rel_types))
                .filter(LexicalUnit.pos > 4)
                .order_by(Synset.id_)
                )
    return mappings
