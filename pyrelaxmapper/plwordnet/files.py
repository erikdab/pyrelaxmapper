# -*- coding: utf-8 -*-
"""plWordNet file data set utilities."""


class Domain:
    """Store domain information.

    Properties
    ----------
    id_ : int
        Surrogate key
    name : str
        Domain name
    description : str
        Domain description
    """
    def __init__(self, id_, name, description):
        self.id_ = id_
        self.name = name
        self.description = description


class POS:
    """Store Part of Speech (POS) information.

    Properties
    ----------
    id_ : int
        Surrogate key
    name : str
        Short POS name
    fullname : str
        Full POS name (in polish)
    domain_ids : list
        List of domain ids to which POS may belong"""
    def __init__(self, id_, name, fullname, domain_ids):
        self.id_ = id_
        self.name = name
        self.fullname = fullname
        self.domain_ids = domain_ids


def load_header_file(file, header):
    """Load data from file according to header titles.

    Currently required the header to be present (to ensure consistency).

    Parameters
    ----------
    file : io.TextIOBase
        File to load data from
    header : list
        List of header titles.
    cls
        Type of class to instantiate
    """
    titles = list(map(str.strip, file.readline().split('\t')))
    if titles != header:
        raise ValueError('File format does not match expected: ' + '\\t'.join(header)
                         + '\nReceived: ' + '\\t'.join(titles))
    objects = []
    for line in file:
        parts = list(map(str.strip, line.split('\t')))
        if line.strip() and len(parts):
            objects.append(parts)
    return objects


# TODO: hoping for domains and POS to be included in the database!
def load_domains(file):
    """Load domains from file."""
    domains = load_header_file(file, ['id', 'name', 'description'])
    return domains


def load_pos(file):
    """Load POS from file."""
    pos = load_header_file(file, ['id', 'name', 'fullname', 'domain_ids'])
    return pos
