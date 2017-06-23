# -*- coding: utf-8 -*-
"""plWordNet file utilities."""


class Domain:
    """Word sense domain.

    Properties
    ----------
    uid : int
        Surrogate key
    char : str
        1-2 characters, ID in string format
    name : str
        Domain name
    description : str
        Domain description
    """
    def __init__(self, uid, char, name, description):
        self.uid = uid
        self.char = char
        self.name = name
        self.description = description


class POS:
    """Part of Speech (POS).

    Properties
    ----------
    uid : int
        Surrogate key
    name : str
        Short POS name
    fullname : str
        Full POS name (in polish)
    domain_ids : list of int
        List of domain ids to which POS may belong.
    """
    def __init__(self, uid, name, fullname, domain_ids):
        self.uid = int(uid)
        self.name = name
        self.fullname = fullname
        self.domain_ids = [int(domain_id) for domain_id in domain_ids]


def load_header_file(file, header):
    """Load data from file according to header titles.

    Currently required the header to be present (to ensure consistency).

    Parameters
    ----------
    file : io.TextIOBase
        File to load data from
    header : list of str
        List of header titles.

    Returns
    -------
    objects : list of list
        List of objects (stored as a list consisting of columns)
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


def load_domains(file):
    """Load domains from file.

    Returns
    -------
    domains : list of Domain
    """
    domains = load_header_file(file, ['id', 'char', 'name', 'description'])
    return [Domain(uid, char, name, description) for uid, char, name, description in domains]


def load_pos(file):
    """Load POS from file.

    Returns
    -------
    pos : list of Pos
    """
    pos = load_header_file(file, ['id', 'name', 'fullname', 'domain_ids'])
    return [POS(uid, name, fullname, description) for uid, name, fullname, description in pos]
