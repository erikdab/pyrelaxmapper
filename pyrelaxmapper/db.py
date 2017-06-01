# -*- coding: utf-8 -*-
"""Database utilities."""
import sqlalchemy
import sqlalchemy.engine.url
import sqlalchemy.orm


def create_engine(settings):
    """Create an SQLAlchemy engine from settings dict."""
    url = sqlalchemy.engine.url.URL(**settings)
    engine = sqlalchemy.create_engine(url)
    engine.echo = False
    return engine


def session_start(engine):
    """Start an SQLAlchemy session."""
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    return Session()
