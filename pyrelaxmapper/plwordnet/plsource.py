# -*- coding: utf-8 -*-
import os

import conf
from plwordnet import files
from pyrelaxmapper.plwordnet import queries
from pyrelaxmapper.wnmap import wnsource


class PLWordNet(wnsource.WordNet):
    """plWordNet WordNet for the MySQL plWN database.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Config Parser with plWordNet config.
    section : str, optional
        Section inside parser which contains plWordNet config.
        Default selects the [source] section.
    """
    def __init__(self, parser, section='source'):
        self._config = self.Config(parser, section)
        self._version = ''

        self._synsets = {}
        self._lunits = {}
        self._reltypes = {}
        self._hypernyms = {}
        self._hypernym_paths = {}
        self._hyponyms = {}
        self._antonyms = {}
        self._pos = {}
        self._domains = {}

        self._load_data()

    class Config:
        """plWordNet WordNet configuration.

        Parameters
        ----------
        parser : configparser.ConfigParser
        section : str, optional
            Section inside parser which contains plWordNet config.
            Default selects the [source] section.
        """
        def __init__(self, parser, section='source'):
            self.db_file = parser[section]['db-file']
            self._pos_file = parser[section]['pos-file']
            self._domain_file = parser[section]['domain-file']
            self._pos = parser['relaxer']['pos']

        def pos_file(self):
            """Filename containing POS information.

            Returns
            -------
            str
            """
            return self._domain_file

        def domain_file(self):
            """Filename containing Domains information.

            Returns
            -------
            str
            """
            return self._domain_file

        def pos(self):
            """Parts of speech to load.

            Returns
            -------
            pos : list of str
            """
            return self._pos

        def session(self):
            """Start a DB connection to plWordNet database.

            Returns
            -------

            """
            return conf.make_session(self.db_file)

    POS = {'v': 1, 'n': 2, 'r': 3, 'a': 4,
           'v_en': 5, 'n_en': 6, 'r_en': 7, 'a_en': 8}

    @staticmethod
    def name_full():
        return 'plWordNet'

    @staticmethod
    def type():
        return 'plwn-sql'

    @staticmethod
    def name():
        return 'plWN'

    def lang(self):
        return 'pl-pl'

    def version(self):
        return self._version

    def synset(self, id_):
        return self._synsets.get(int(id_))

    def synsets(self, lemma, pos=None):
        return [synset for synset in self._synsets.values() if lemma in synset.lemma_names()]

    def lunits_all(self):
        return self._lunits.values()

    def all_synsets(self):
        return self._synsets.values()

    def all_hypernyms(self):
        return self._hypernyms.items()

    def all_hyponyms(self):
        return self._hyponyms.items()

    def hypernyms(self, id_):
        return self._hypernyms.get(int(id_), [])

    def hypernym_paths(self, id_):
        return self._hypernym_paths.get(int(id_), [])

    def hyponyms(self, id_):
        return self._hyponyms.get(int(id_), [])

    def hyponym_layers(self, id_):
        return self._hyponym_layers.get(int(id_), [])

    def antonyms(self, id_):
        return self._antonyms.get(int(id_), [])

    def mappings(self, other_wn):
        """Existing mappings with another wordnet.

        Parameters
        ----------
        other_wn : str
            Short name of target WordNet to look for existing mappings to.
        """
        if other_wn in ['PWN', 'WordNet']:
            session = self._config.session()
            return [self.synset(row.id_) for row in queries.pwn_mappings(session).all()]
        return None

    def _load_data(self):
        """Load plWordNet data from MySQL."""
        session = self._config.session()

        if not self._synsets:
            pos = []
            for uid in self._config.pos():
                pos.append(self.POS[uid])

            # Lexical Units
            lunits_query = queries.lunits(session, pos)
            self._lunits = {lunit.id_: PLLexicalUnit(lunit.id_, lunit.lemma, lunit.pos)
                            for lunit in lunits_query}

            # Synsets
            synsets_query = queries.synsets(session, pos)
            self._synsets = {int(unitindex): int(lex_id)
                             for synset in synsets_query
                             for lex_id, unitindex in
                             zip(synset.lex_ids.split(','), synset.unitindexes.split(','))}

            # Relation Types
            reltypes_query = queries.reltypes(session)
            self._reltypes = {reltype.name: reltype for reltype in reltypes_query}

            # Synset Relations:
            # This looks reversed, but is actually appropriate.
            hyper_query = queries.synset_relations(session, self._reltypes['hiponimia'].id_, pos)
            hypo_query = queries.synset_relations(session, self._reltypes['hiperonimia'].id_, pos)

            self._hypernyms = {}
            self._hyponyms = {}
            for hypernym in hyper_query:
                self._hypernyms.setdefault(hypernym.parent_id, []).append(
                    self.synset(hypernym.child_id))
            for hyponym in hypo_query:
                self._hyponyms.setdefault(hyponym.parent_id, []).append(
                    self.synset(hyponym.child_id))

            self._hyponym_layers = {synset.id_(): self._find_hyponym_layers(synset)
                                    for synset in self._synsets.values()}
            self._hypernym_paths = {synset.id_(): self._find_hypernym_paths(synset)
                                    for synset in self._synsets.values()}

            # Lexical Relations:
            antonyms = queries.lexical_relations(session, pos,
                                                 self._reltypes['antonimia właściwa'].id_)

            for antonym in antonyms:
                self._antonyms.setdefault(antonym.parent_id, []).append(
                    self._lunits[antonym.child_id])

        if not self._pos:
            with open(os.path.expanduser(self._config.pos_file())) as file:
                self._pos = files.load_pos(file)

        if not self._domains:
            with open(os.path.expanduser(self._config.domain_file())) as file:
                self._pos = files.load_pos(file)

        if not self._version:
            self._version = queries.version(session)

    def _find_hyponym_layers(self, synset):
        """Find hyponym layers for synset.

        Parameters
        ----------
        synset : pyrelaxmapper.wnmap.wnsource.Synset

        Returns
        -------
        hipo_layers : list of pyrelaxmapper.wnmap.wnsource.Synset
        """
        todo = [synset]
        hipo_layers = []
        while todo:
            do_next = []
            for node in todo:
                do_next.extend(node.hyponyms())
            todo = do_next
            if todo:
                hipo_layers.append(todo)
        return hipo_layers

    def _find_hypernym_paths(self, synset):
        """Find hypernym paths for synset.

        Parameters
        ----------
        synset : pyrelaxmapper.wnmap.wnsource.Synset

        Returns
        -------
        hyper_paths : list of pyrelaxmapper.wnmap.wnsource.Synset
        """
        hypernyms = synset.hypernyms()
        if not hypernyms:
            return [[synset]]
        hypernym_paths = []
        idx = 0
        for idx, hypernym in enumerate(synset.hypernyms()):
            sub_paths = [path + [synset] for path in self._find_hypernym_paths(hypernym)]
            hypernym_paths.append(sub_paths)

        return [hypernym_path[0] for hypernym_path in hypernym_paths] if idx else hypernym_paths[0]


class PLSynset(wnsource.Synset):
    """plWordNet Synset for the MySQL plWN database.

    Parameters
    ----------
    plwordnet : PLWordNet
    uid : int
        Unique identifier
    lunits: dict
        Lexical units
    """

    def __init__(self, plwordnet, uid, lunits):
        self._plwordnet = plwordnet
        self._uid = uid
        self._lunits = lunits

    def uid(self):
        return self._uid

    def name(self):
        return self._uid

    def lemmas(self):
        return self._lunits.values()

    def lemma_names(self):
        return [lunit.name() for lunit in self._lunits.values()]

    def hypernyms(self):
        return self._plwordnet.hypernyms(self._uid)

    def hypernym_paths(self):
        return self._plwordnet.hypernym_paths(self._uid)

    def hyponyms(self):
        return self._plwordnet.hyponyms(self._uid)

    def hyponym_layers(self):
        return self._plwordnet.hyponym_layers(self._uid)

    def antonyms(self):
        return [antonym.name()
                for unit_id in self._lunits
                for antonym in self._plwordnet.antonyms(unit_id)]

    def pos(self):
        return self._lunits[0].pos() if self._lunits else 0


class PLLexicalUnit(wnsource.Lemma):
    """plWordNet lexical unit for the MySQL plWN database.

    Parameters
    ----------
    uid : int
        Lexical Unit unique identifier.
    lemma : str
        Lemma of Lexical Unit
    pos : str
        Lexical Unit pos
    """

    def __init__(self, uid, lemma, pos):
        self._uid = uid
        self._lemma = lemma
        self._pos = pos

    def id_(self):
        return self._uid

    def name(self):
        return self._lemma

    def pos(self):
        return self._pos
