# -*- coding: utf-8 -*-
"""Database utilities."""
import sqlalchemy
import sqlalchemy.engine.url
import sqlalchemy.orm


def create_engine(settings):
    """Create an UTF-8 SQLAlchemy engine from settings dict."""
    if 'mysql' in settings['drivername']:
        settings['query'] = {'charset': 'utf8mb4'}
    url = sqlalchemy.engine.url.URL(**settings)
    engine = sqlalchemy.create_engine(url, echo=False)
    return engine


def session_start(engine):
    """Start an SQLAlchemy session."""
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    return Session()
