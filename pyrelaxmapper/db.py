# -*- coding: utf-8 -*-

"""plWordNet database utilities."""

import sqlalchemy
import sqlalchemy.engine.url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Parameter(Base):
    """Stores database parameters."""
    __tablename__ = 'parameter'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    value = Column(String(255))


def connect(conf):
    """Create SQLAlchemy engine from settings dict."""
    conf['drivername'] = 'mysql'
    url = sqlalchemy.engine.url.URL(**conf)
    db = sqlalchemy.create_engine(url)
    db.echo = False
    return db


def plwn_version(db):
    """Query for plWordnet DB version."""
    Session = sessionmaker(bind=db)
    session = Session()
    parameter = session.query(Parameter).filter_by(name='programversion').first()
    return parameter.value
