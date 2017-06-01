# -*- coding: utf-8 -*-
"""plWordNet DB queries."""
from . import models


def version(session):
    """Query plWordNet for format version."""
    parameter = session.query(models.Parameter).filter_by(name='programversion').first()
    return parameter.value
