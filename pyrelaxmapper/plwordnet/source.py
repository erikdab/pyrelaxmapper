# -*- coding: utf-8 -*-
from pyrelaxmapper.plwordnet import queries
from pyrelaxmapper.rlabel import wordnet


# Could load all, then allow to cache it all into a pickle objects.
class PLWordNet(wordnet.RLWordNet):
    """plWordNet WordNet interface."""

    # Constants
    RELATION_TYPES = {'hypernyms': 10, 'hyponyms': 11}
    POS = {'v': 5, 'n': 6, 'r': 7, 'a': 8}

    def __init__(self, session, config, preload=False):
        self._session = session
        self._config = config
        self._version = None
        self._synsets = None
        # self._mappings = None
        self._lunits = None
        self._reltypes = None
        # self._reltypes_name = None
        self._hypernyms = None
        self._hyponyms = None
        # self._domains = None
        # self._pos = None
        if preload:
            self._require_data('all')

    def __str__(self):
        return self._version

    def __repr__(self):
        return self._version

    def __getstate__(self):
        """Return state values to be pickled."""
        return (self._version, self._synsets, self._lunits, self._reltypes,
                self._hypernyms, self._hyponyms)
        # , self._mappings , self._domains, self._pos

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        (self._version, self._synsets, self._lunits, self._reltypes,
         self._hypernyms, self._hyponyms) = state
        # , self._mappings, self._domains, self._pos

    def open(self):
        """Initializes access to WordNet data."""
        pass

    def close(self):
        """Cleans up after use."""
        pass

    def version(self):
        """WordNet version."""
        self._require_data('version')
        return self._version

    def synset(self, id_, pos=None):
        """Find synset with id."""
        self._require_data('synsets')
        return self._synsets[id_]

    def synsets(self, lemma, pos=None):
        """Return all synsets including given lemma and part of speech."""
        pass

    def hypernyms(self, id_):
        self._require_data('hypernyms')
        return self._hypernyms[id_] if id_ in self._hypernyms else []

    def hyponyms(self, id_):
        self._require_data('hyponyms')
        return self._hyponyms[id_] if id_ in self._hyponyms else []

    def synsets_all(self):
        self._require_data('synsets')
        return self._synsets

    # def mappings(self):
    #     self._require_data('mappings')
    #     return self._mappings

    # def pos(self):
    #     """All POS."""
    #     self._require_data('pos')
    #     return self._pos
    #
    # def domains(self):
    #     """All domains."""
    #     self._require_data('domains')
    #     return self._domains

    # Should take into account pos we want to load.
    # Should hash and then put into dictionary.
    # Should return Synset object which is an adapter to the plWN DB Synset
    # Eventually SHOULD USE load as Models with their mappings! encapsulated in PLObjects
    def _require_data(self, names=None):
        """Ensure dataset from names are loaded.

        Parameters
        ----------
        names
            Dataset names to load if not yet loaded.
            'all' to load all
        """
        if not isinstance(names, list):
            names = [names]

        if any(name in ['lunits', 'all'] for name in names) and not self._lunits:
            # pos = [1, 2, 3, 4]
            pos = [2, 6]
            # Lexical Units
            lunits = queries.lunits(self._session, pos)
            if lunits:
                self._lunits = {}
                for lunit in lunits:
                    self._lunits[lunit.id_] = PLLexicalUnit(lunit.id_, lunit.lemma, lunit.pos)

            # Synsets
            synsets = queries.synsets2(self._session, pos)
            self._synsets = {}
            for synset in synsets:
                syn_lunits = {}
                for lex_id, unitindex in zip(synset.lex_ids.split(','),
                                             synset.unitindexes.split(',')):
                    syn_lunits[int(unitindex)] = self._lunits[int(lex_id)]
                self._synsets[synset.id_] = PLSynset(self, synset.id_, syn_lunits)

            # Relation Types
            # Don't need all of them? Only PL? And those used in the algorithm!
            reltypes = queries.relationtypes(self._session)
            if reltypes:
                self._reltypes = {}
                for reltype in reltypes:
                    self._reltypes[reltype.name] = reltype

            # Relations, only non plWN-PWN?
            hypernyms = queries.synset_relations2(self._session, self._reltypes['hiperonimia'].id_,
                                                  pos)
            hyponyms = queries.synset_relations2(self._session, self._reltypes['hiponimia'].id_,
                                                 pos)
            self._hypernyms = {}
            self._hyponyms = {}
            for hypernym in hypernyms:
                self._hypernyms.setdefault(hypernym.parent_id, []).append(
                    self._synsets[hypernym.child_id])
            for hyponym in hyponyms:
                self._hyponyms.setdefault(hyponym.parent_id, []).append(
                    self._synsets[hyponym.child_id])

        # if any(name in ['synsets', 'all'] for name in names) and not self._synsets:
        #     _synsets = queries.synsets(self._session).all()
        #     # for synset in _synsets:
        #
        # if any(name in ['hypernyms', 'all'] for name in names) and not self._hypernyms:
        #     self._hypernyms = queries.synset_relations(self._session, [10]).all()
        #
        # if any(name in ['hyponyms', 'all'] for name in names) and not self.hyponyms:
        #     self._hyponyms = queries.synset_relations(self._session, [11]).all()
        #
        # if any(name in ['mappings', 'all'] for name in names) and not self._mappings:
        #     self._mappings = queries.pwn_mappings(self._session).all()

        # if any(name in ['pos', 'all'] for name in names) and not self._pos:
        #     with open(os.path.expanduser(self._config['path']['pos'])) as file:
        #         self._pos = files.load_pos(file)
        #
        # if any(name in ['domains', 'all'] for name in names) and not self._domains:
        #     with open(os.path.expanduser(self._config['path']['domains'])) as file:
        #         self._domains = files.load_domains(file)

        if any(name in ['version', 'all'] for name in names) and not self._version:
            self._version = queries.version(self._session)


class PLSynset(wordnet.RLSynset):
    """plWordNet Synset interface.

    Parameters
    ----------
    plwordnet : PLWordNet
        PLWordNet source.
    id_
        Synset id
    lunits: dict
        Synset lexical unit ids
    """

    def __init__(self, plwordnet, id_=None, lunits=None):
        self._plwordnet = plwordnet
        self._id = id_
        self._lunits = lunits
        # self._hypernyms = set()
        # self._hyponyms = set()

    def id_(self):
        return self._id

    def __str__(self):
        return str(self._id)

    def __repr__(self):
        return str(self._id)

    def lemmas(self):
        return self._lunits

    def lemma_ids(self):
        return self._lunits.keys()

    # def lemma_names(self):
    #     return self._lu_names

    def hypernyms(self):
        return self._plwordnet.hypernyms(self._id)

    def hyponyms(self):
        return self._plwordnet.hyponyms(self._id)

    def definition(self):
        pass

    def examples(self):
        pass

    def min_depth(self):
        pass


class PLLexicalUnit(wordnet.RLLexicalUnit):
    """Relaxtion labeling Lexical Unit interface."""

    def __init__(self, id_, lemma, pos):
        self._id = id_
        self._lemma = lemma
        self._pos = pos

    def id_(self):
        """Identifier."""
        return self._id

    def __str__(self):
        return str(self._id)

    def __repr__(self):
        return str(self._id)

    def lemma(self):
        """Lemma."""
        return self._lemma

    def pos(self):
        """Part of speech."""
        return self._pos
