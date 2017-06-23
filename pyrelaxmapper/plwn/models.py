# -*- coding: utf-8 -*-
"""plWordNet database models and external data classes."""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Parameter(Base):
    """Stores database parameters.

    Properties
    ----------
    id_ : Column(Integer)
        Surrogate key
    name : Column(String(255))
        Name of parameter
    value : Column(String(255))
        Value of parameter"""
    __tablename__ = 'parameter'

    id_ = Column('id', Integer, primary_key=True)
    name = Column(String(255))
    value = Column(String(255))


class LexicalUnit(Base):
    """Stores lexical units.

    Parameters
    ----------
    id_ : Column(Integer)
        Surrogate key
    lemma : Column(String(255))
        Lemma form of lexical unit
    domain : Column(Integer)
        Domain ID
    pos : Column(Integer)
        POS ID"""
    __tablename__ = 'lexicalunit'

    id_ = Column('id', Integer, primary_key=True)
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
    parent_id : Column(Integer)
        Relation parent ID (source)
    child_id : Column(Integer)
        Relation child ID (target)
    rel_id : Column(Integer)
        Relation type ID
    valid : Column(Integer)
        Relation validity (1-yes, 0-no)"""
    __tablename__ = 'lexicalrelation'

    parent_id = Column(Integer, ForeignKey('lexicalunit.id'), primary_key=True)
    child_id = Column(Integer, ForeignKey('lexicalunit.id'), primary_key=True)
    rel_id = Column(Integer, ForeignKey('relationtype.id'))
    valid = Column(Integer)


class Synset(Base):
    """Stores synsets.

    Properties
    ----------
    id_ : Column(Integer)
        Surrogate key
    unitsstr : Column(String(1024))
        String describing synset"""
    __tablename__ = 'synset'

    id_ = Column('id', Integer, primary_key=True)
    definition = Column(String(1024))
    unitsstr = Column(String(1024))


class SynsetRelation(Base):
    """Stores synset relations.

    Properties
    ----------
    parent_id : Column(Integer)
        Relation parent ID (source)
    child_id : Column(Integer)
        Relation child ID (target)
    rel_id : Column(Integer)
        Relation type ID
    valid : Column(Integer)
        Relation validity (1-yes, 0-no)"""
    __tablename__ = 'synsetrelation'

    parent_id = Column(Integer, ForeignKey('synset.id'), primary_key=True)
    child_id = Column(Integer, ForeignKey('synset.id'), primary_key=True)
    rel_id = Column(Integer, ForeignKey('relationtype.id'))
    valid = Column(Integer)


# TODO: Fix autoreverse docstring
class RelationType(Base):
    """Stores all lexical and synset relation types.

    Parameters
    ----------
    id_ : Column(Integer)
        Surrogate key
    parent_id : Column(Integer)
        Relation parent ID
    reverse_id : Column(Integer)
        Relation child ID
    name : Column(String(255))
        Relation name
    description : Column(String(255))
        Relation description
    posstr : Column(String(255))
        Parts of speech which may have such a relation
    autoreverse : Column(Integer)
        Whether the relation is reversable
    shortcut : Column(String(255))
        Short relation name
    """
    __tablename__ = 'relationtype'

    id_ = Column('id', Integer, primary_key=True)
    # 0,1,2
    # objecttype = Column(Integer)
    parent_id = Column(Integer, ForeignKey('relationtype.id'))
    reverse_id = Column(Integer, ForeignKey('relationtype.id'))
    name = Column(String(255))
    # description = Column(String(500))
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
    lex_id : Column(Integer)
        Lexical Unit ID
    syn_id : Column(Integer)
        Synset ID
    unitindex : Column(Integer)
        Lexical Unit's number inside synset"""
    __tablename__ = 'unitandsynset'

    lex_id = Column(Integer, ForeignKey('lexicalunit.id'))
    syn_id = Column(Integer, ForeignKey('synset.id'), primary_key=True)
    unitindex = Column(Integer, primary_key=True)
