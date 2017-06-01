# -*- coding: utf-8 -*-
"""plWordNet database utilities."""
import sqlalchemy
import sqlalchemy.engine.url
from sqlalchemy.orm import sessionmaker
from plwordnet import models as plwn


def create_engine(settings):
    """Create an SQLAlchemy engine from settings dict."""
    url = sqlalchemy.engine.url.URL(**settings)
    db = sqlalchemy.create_engine(url)
    db.echo = False
    return db


def query_version(db):
    """Query plWordNet format version."""
    Session = sessionmaker(bind=db)
    session = Session()
    parameter = session.query(plwn.Parameter).filter_by(name='programversion').first()
    return parameter.value
