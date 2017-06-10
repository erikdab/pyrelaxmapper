# -*- coding: utf-8 -*-
from pyrelaxmapper.plwordnet import queries
from pyrelaxmapper.rlabel import rlsource


# Could load all, then allow to cache it all into a pickle objects.
class PLWordNet(rlsource.RLWordNet):
    """plWordNet WordNet interface."""

    RELATION_TYPES = {'hypernyms': 10, 'hyponyms': 11}
    POS = {'v': 1, 'n': 2, 'r': 3, 'a': 4,
           'v_en': 5, 'n_en': 6, 'r_en': 7, 'a_en': 8}

    def __init__(self, session):
        self._version = ''
        self._synsets = {}
        self._lunits = {}
        self._reltypes = {}
        self._hypernyms = {}
        self._hypernym_paths = {}
        self._hyponyms = {}
        self._load_data(session)

    def version(self):
        return self._version

    def synset(self, id_):
        return self._synsets[id_]

    def synsets(self, lemma, pos=None):
        pass

    def synsets_all(self):
        return self._synsets

    def hypernyms(self, id_):
        return self._hypernyms[id_] if id_ in self._hypernyms else []

    def hypernym_paths(self, id_):
        return self._hypernym_paths[id_] if id_ in self._hypernym_paths else []

    def hyponyms(self, id_):
        return self._hyponyms[id_] if id_ in self._hyponyms else []

    # Should take into account pos we want to load.
    # Should hash and then put into dictionary.
    # Should return Synset object which is an adapter to the plWN DB Synset
    # Eventually SHOULD USE load as Models with their mappings! encapsulated in PLObjects
    def _load_data(self, session):
        """Ensure dataset from names are loaded.

        Parameters
        ----------
        session : sqlalchemy.orm.session.Session
        """
        if not self._lunits:
            pos = [self.POS['n'], self.POS['n_en']]
            # Lexical Units
            lunits = queries.lunits(session, pos)
            self._lunits = {}
            for lunit in lunits:
                self._lunits[lunit.id_] = PLLexicalUnit(lunit.id_, lunit.lemma, lunit.pos)

            # Synsets
            # TODO: Figure out how to have synset name somehow for visual presentation.
            synsets = queries.synsets2(session, pos)
            self._synsets = {}
            for synset in synsets:
                syn_lunits = {}
                for lex_id, unitindex in zip(synset.lex_ids.split(','),
                                             synset.unitindexes.split(',')):
                    syn_lunits[int(unitindex)] = self._lunits[int(lex_id)]
                self._synsets[synset.id_] = PLSynset(self, synset.id_, syn_lunits)

            # Relation Types
            # TODO: Don't need all of them? Only PL? And those used in the algorithm!
            reltypes = queries.relationtypes(session)
            self._reltypes = {}
            for reltype in reltypes:
                self._reltypes[reltype.name] = reltype

            # Relations:
            # Load:
            hypernyms = queries.synset_relations2(session, self._reltypes['hiperonimia'].id_,
                                                  pos)
            hyponyms = queries.synset_relations2(session, self._reltypes['hiponimia'].id_,
                                                 pos)
            # Aggregate: (in SQL column was too long!)
            self._hypernyms = {}
            self._hyponyms = {}
            for hypernym in hypernyms:
                self._hypernyms.setdefault(hypernym.parent_id, []).append(
                    self.synset(hypernym.child_id))
            for hyponym in hyponyms:
                self._hyponyms.setdefault(hyponym.parent_id, []).append(
                    self.synset(hyponym.child_id))

            # TODO: Fake for now: Should work more or less though
            # Not sure if plWordNet has paths multiple hypernym paths per synset?
            # Need to check it out!
            self._hypernym_paths = {}
            for synset in self._synsets.values():
                do_now = [synset]
                hypernym_paths = []
                while do_now:
                    do_next = []
                    for node in do_now:
                        do_next.extend(node.hypernyms())
                    do_now = do_next
                    hypernym_paths.extend(do_next)
                self._hypernym_paths[synset.id_()] = [hypernym_paths]

        # if any(name in ['mappings', 'all'] for name in names) and not self._mappings:
        #     self._mappings = queries.pwn_mappings(self._session).all()

        # if any(name in ['pos', 'all'] for name in names) and not self._pos:
        #     with open(os.path.expanduser(self._config['path']['pos'])) as file:
        #         self._pos = files.load_pos(file)
        #
        # if any(name in ['domains', 'all'] for name in names) and not self._domains:
        #     with open(os.path.expanduser(self._config['path']['domains'])) as file:
        #         self._domains = files.load_domains(file)

        if not self._version:
            self._version = queries.version(session)


# Figure out how to have name!
class PLSynset(rlsource.RLSynset):
    """plWordNet Synset interface.

    Parameters
    ----------
    plwordnet : PLWordNet
    id_ : int
        Unique identifier
    lunits: list
        Lexical units
    """
    def __init__(self, plwordnet, id_, lunits):
        self._plwordnet = plwordnet
        self._id = id_
        self._lunits = lunits

    def id_(self):
        return self._id

    def name(self):
        return self._id

    def lemmas(self):
        return self._lunits

    def lemma_names(self):
        return [lunit.name() for lunit in self._lunits]

    def hypernyms(self):
        return self._plwordnet.hypernyms(self._id)

    def hypernym_paths(self):
        return self._plwordnet.hypernym_paths(self._id)

    def min_depth(self):
        pass

    def hyponyms(self):
        return self._plwordnet.hyponyms(self._id)

    def pos(self):
        return self._lunits[0].pos() if self._lunits else 0


class PLLexicalUnit(rlsource.RLLexicalUnit):
    """plWN RL Source Lexical Unit.

    Parameters
    ----------
    id_ : int
        Lexical Unit unique identifier.
    lemma : str
        Lemma of Lexical Unit
    pos : int or str
        Lexical Unit pos
    """
    def __init__(self, id_, lemma, pos):
        self._id = id_
        self._lemma = lemma
        self._pos = pos

    def id_(self):
        return self._id

    def name(self):
        return self._lemma

    def pos(self):
        return self._pos
