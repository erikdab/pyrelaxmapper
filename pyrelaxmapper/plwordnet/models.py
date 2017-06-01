# -*- coding: utf-8 -*-
"""plWordNet database and external data models."""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()


class Parameter(Base):
    """Stores database parameters.

    Properties
    ----------
    id_ : int
        Surrogate key
    name : String
        Name of parameter
    value : String
        Value of parameter"""
    __tablename__ = 'parameter'

    id_ = Column(Integer, primary_key=True)
    name = Column(String(255))
    value = Column(String(255))


class LexicalUnit(Base):
    """Stores lexical units.

    Parameters
    ----------
    id_ : int
        Surrogate key
    lemma : str
        Lemma form of lexical unit
    domain : int
        Domain ID
    pos : int
        POS ID"""
    __tablename__ = 'synset'

    id_ = Column(Integer, primary_key=True)
    lemma = Column(String(255))
    domain = Column(Integer)
    pos = Column(Integer)
    # Add later if desired:
    # 0-manual, 1-automatic?
    # source = Column(Integer)
    # 0,1,2,3,4,5
    # status = Column(Integer)
    # comment = Column(String(2048))
    # 1-59: is this the variant of a meaning? polysemous, etc.?
    # variant = Column(Integer)
    # -1,0,1,2,3,4: added in which project
    # If used, add also class Project
    # project = Column(Integer)
    # empty now
    # owner = Column(Integer)


class LexicalRelation(Base):
    """Stores lexical relations.

    Parameters
    ----------
    parent_id : int
        Relation parent ID (source)
    child_id : int
        Relation child ID (target)
    rel_id : int
        Relation type ID
    valid : int
        Relation validity (1-yes, 0-no)"""
    __tablename__ = 'synsetrelation'

    parent_id = Column(Integer, primary_key=True)
    child_id = Column(Integer, primary_key=True)
    rel_id = Column(Integer)
    valid = Column(Integer)


class Synset(Base):
    """Stores synsets.

    Properties
    ----------
    id_ : int
        Surrogate key
    unitsstr : str
        String describing synset"""
    __tablename__ = 'synset'

    id_ = Column(Integer, primary_key=True)
    unitsstr = Column(String(1024))


class SynsetRelation(Base):
    """Stores synset relations.

    Properties
    ----------
    parent_id : int
        Relation parent ID (source)
    child_id : int
        Relation child ID (target)
    rel_id : int
        Relation type ID
    valid : int
        Relation validity (1-yes, 0-no)"""
    __tablename__ = 'synsetrelation'

    parent_id = Column(Integer, primary_key=True)
    child_id = Column(Integer, primary_key=True)
    rel_id = Column(Integer)
    valid = Column(Integer)


# TODO: Fix autoreverse docstring
class RelationType(Base):
    """Stores all lexical and synset relation types.

    Parameters
    ----------
    id_ : int
        Surrogate key
    parent_id : int
        Relation parent ID
    reverse_id : int
        Relation child ID
    name : str
        Relation name
    posstr : str
        Parts of speech which may have such a relation
    autoreverse : int
        Whether the relation is reversable
    shortcut : str
        Short relation name
    """
    id_ = Column(Integer, primary_key=True)
    # 0,1,2
    # objecttype = Column(Integer)
    parent_id = Column(Integer)
    reverse_id = Column(Integer)
    name = Column(String(255))
    description = Column(String(500))
    posstr = Column(String(255))
    autoreverse = Column(Integer)
    # How to display relationship information.
    # display = Column(String(255))
    shortcut = Column(String(255))
    # PWN relation symbol
    # pwn = Column(String(10))
    # What is this?
    # order = Column(Integer)


class UnitSynset(Base):
    """Stores relationships between lexical units and synsets.

    Properties
    ----------
    lex_id : int
        Lexical Unit ID
    syn_id : int
        Synset ID
    unitindex : int
        Lexical Unit's number inside synset"""
    __tablename__ = 'unitandsynset'

    lex_id = Column(Integer)
    syn_id = Column(Integer, primary_key=True)
    unitindex = Column(Integer, primary_key=True)
