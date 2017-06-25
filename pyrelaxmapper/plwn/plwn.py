# -*- coding: utf-8 -*-
import os
import logging

from pyrelaxmapper import wordnet, utils
from pyrelaxmapper.plwn import queries, files

logger = logging.getLogger()


class PLWordNet(wordnet.WordNet):
    """plWordNet WordNet for the MySQL plWN database.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Config Parser with plWordNet config.
    section : str, optional
        Section inside parser which contains plWordNet config.
        Default selects the [source] section.
    """

    def __init__(self, parser, section, preload=True):
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

        self._loaded = False
        super().__init__(parser, section, preload)

    # Add tests, plus option to not set all.
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
            if not parser.has_option(section, 'db-file'):
                raise KeyError('plWordNet ({}) config requires the "db-file" option.'
                               .format(PLWordNet.uid()))
            self.db_file = os.path.expanduser(parser[section]['db-file'])
            self._pos_file = None
            if parser.has_option(section, 'pos-file'):
                self._pos_file = os.path.expanduser(parser[section]['pos-file'])
            self._domain_file = None
            if parser.has_option(section, 'domain-file'):
                self._domain_file = os.path.expanduser(parser[section]['domain-file'])
            self._pos = parser['relaxer']['pos'].split(',')

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

        def make_session(self):
            """Start a DB connection to plWordNet database.

            Returns
            -------

            """
            return utils.make_session(self.db_file)

    POS = {'v': 1, 'n': 2, 'r': 3, 'a': 4,
           'v_en': 5, 'n_en': 6, 'r_en': 7, 'a_en': 8}

    @staticmethod
    def name_full():
        return 'plWordNet'

    @staticmethod
    def name():
        return 'plWN'

    @staticmethod
    def uid():
        return 'plwn-sql'

    def lang(self):
        return 'pl-pl'

    def version(self):
        if not self._version:
            self._version = queries.version(self._config.make_session())
        return self._version

    def synset(self, id_):
        return self._synsets.get(int(id_))

    def synsets(self, lemma, pos=None):
        return (synset for synset in self._synsets.values() if lemma in synset.lemma_names())

    def all_lunits(self):
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

    def hypernym_layers(self, id_, uid=False):
        if uid:
            return self._hypernym_layers_uid.get(int(id_), [])
        else:
            return self._hypernym_layers.get(int(id_), [])

    def hyponyms(self, id_):
        return self._hyponyms.get(int(id_), [])

    def hyponym_layers(self, id_, uid=False):
        if uid:
            return self._hyponym_layers_uid.get(int(id_), [])
        else:
            return self._hyponym_layers.get(int(id_), [])

    def antonyms(self, id_):
        return self._antonyms.get(int(id_), [])

    def mappings(self, other_wn, recurse=True):
        """Existing mappings with another wordnet.

        Parameters
        ----------
        other_wn : pyrelaxmapper.wordnet.WordNet
            Short name of target WordNet to look for existing mappings to.
        recurse : bool
            Whether to check the other wordnet, only once

        Returns
        -------
        dict
        """
        target_name = other_wn.name()
        if target_name in ['PWN', 'WordNet']:
            session = self._config.make_session()
            return {row.id_: row.unitsstr
                    for row in queries.pwn_mappings(session).all()}
        return super().mappings(other_wn, False)

    def load(self):
        """Load plWordNet data from MySQL."""

        # Create method to read this
        if not self._pos and self._config.pos_file():
            with open(self._config.pos_file()) as file:
                self._pos = files.load_pos(file)

        if not self._domains and self._config.domain_file():
            with open(self._config.domain_file()) as file:
                self._domains = files.load_domains(file)

        session = self._config.make_session()

        if not self._synsets:
            pos = []
            for uid in self._config.pos():
                pos.append(self.POS[uid])

            # Lexical Units
            # TODO: Glosses
            logger.info('{} Loading lexical units.'.format(type(self).__name__))
            self._lunits = {lunit.id_: PLLexicalUnit(self, lunit.id_, lunit.lemma, lunit.pos,
                                                     lunit.domain)
                            for lunit in queries.lunits(session, pos)}

            # Synsets
            # TODO: definition could probably be useful, unitsstr maybe?
            logger.info('{} Loading synsets.'.format(type(self).__name__))
            self._synsets = {}
            for synset in queries.synsets(session, pos):
                s_lunits = {int(unitindex): self._lunits[int(lex_id)]
                            for lex_id, unitindex in
                            zip(synset.lex_ids.split(','), synset.unitindexes.split(','))}
                self._synsets[synset.id_] = PLSynset(self, synset.id_, synset.definition, s_lunits)

            # Relation Types
            self._reltypes = {reltype.name: reltype for reltype in queries.reltypes(session)}

            # Synset Relations:
            logger.info('{} Loading hyper/hypo relations.'.format(type(self).__name__))
            self._hypernyms = {}
            self._hyponyms = {}
            for hypernym in queries.synset_relations(session, self._reltypes['hiperonimia'].id_,
                                                     pos):
                self._hypernyms.setdefault(hypernym.child_id, []).append(
                    self.synset(hypernym.parent_id))
            for hyponym in queries.synset_relations(session, self._reltypes['hiponimia'].id_, pos):
                self._hyponyms.setdefault(hyponym.child_id, []).append(
                    self.synset(hyponym.parent_id))

            logger.info('{} Calculating hyponym layers.'.format(type(self).__name__))
            self._hyponym_layers = {synset.uid(): synset.find_hyponym_layers()
                                    for synset in self._synsets.values()}
            self._hyponym_layers_uid = {key: PLSynset.get_uids(values)
                                        for key, values in self._hyponym_layers.items()}
            logger.info('{} Calculating hipernym paths.'.format(type(self).__name__))
            self._hypernym_paths = {synset.uid(): self._find_hypernym_paths(synset)
                                    for synset in self._synsets.values()}
            logger.info('{} Calculating hipernym layers.'.format(type(self).__name__))
            self._hypernym_layers = {synset.uid(): self._find_hypernym_layers(synset)
                                     for synset in self._synsets.values()}
            self._hypernym_layers_uid = {key: PLSynset.get_uids(values)
                                         for key, values in self._hypernym_layers.items()}

            # Lexical Relations:
            logger.info('{} Loading antonymy relations.'.format(type(self).__name__))
            antonym_relid = self._reltypes['antonimia'].id_
            for antonym in queries.lexical_relations(session, antonym_relid, pos):
                self._antonyms.setdefault(antonym.child_id, []).append(
                    self._lunits[antonym.parent_id])

        if not self._version:
            self._version = queries.version(self._config.make_session())

        self._loaded = True
        return self

    def loaded(self):
        return self._loaded

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

    def _find_hypernym_layers(self, synset):
        """Find hypernym paths for synset.

        Parameters
        ----------
        synset : pyrelaxmapper.wnmap.wnsource.Synset

        Returns
        -------
        hyper_paths : list of pyrelaxmapper.wnmap.wnsource.Synset
        """
        paths = synset.hypernym_paths()
        layers = [set() for layer in range(max(len(path) for path in paths) - 1)]
        for path in paths:
            # Bottom to Top; Remove current synset
            path_ = path[::-1][1:]
            for layer in range(len(path_)):
                layers[layer].add(path_[layer])
        return [list(layer) for layer in layers]

    def count_synsets(self):
        """Count of all synsets.

        Returns
        -------
        int
        """
        return len(self._synsets)

    def count_lunits(self):
        """Count of all lunits.

        Returns
        -------
        int
        """
        return len(self._lunits)

    def count_lemmas(self):
        """Count of all lunits.

        Returns
        -------
        int
        """
        lemmas = set()
        lemmas.update(lunit.name() for lunit in self.all_lunits())
        return len(lemmas)


class PLSynset(wordnet.Synset):
    """plWordNet Synset for the MySQL plWN database.

    Parameters
    ----------
    plwordnet : PLWordNet
    uid : int
        Unique identifier
    definition : str
        Definition
    lunits: dict
        Lexical units
    """

    def __init__(self, plwordnet, uid, definition, lunits):
        self._plwordnet = plwordnet
        self._uid = uid
        self._definition = definition if definition and 'brak danych' not in definition else ''
        self._lunits = lunits
        self._hypo = None
        self._hyper = None

    def uid(self):
        return self._uid

    def lemmas(self):
        return iter(self._lunits.values())

    def lemma_names(self):
        return (lunit.name() for lunit in self._lunits.values())

    def hypernyms(self):
        return self._plwordnet.hypernyms(self._uid)

    def hypernym_paths(self):
        return self._plwordnet.hypernym_paths(self._uid)

    def hypernym_layers(self, uid=False):
        if self._hyper is None:
            self._hyper = self._plwordnet.hypernym_layers(self._uid, uid)
        return self._hyper

    def hyponyms(self):
        return self._plwordnet.hyponyms(self._uid)

    def hyponym_layers(self, uid=False):
        if self._hypo is None:
            self._hypo = self._plwordnet.hyponym_layers(self._uid, uid)
        return self._hypo

    def antonyms(self):
        return (antonym.name()
                for lunit in self._lunits.values()
                for antonym in lunit.antonyms())

    def pos(self):
        return self._lunits[0].pos() if self._lunits else 0


class PLLexicalUnit(wordnet.LexicalUnit):
    """plWordNet lexical unit for the MySQL plWN database.

    Parameters
    ----------
    plwordnet : PLWordNet
    uid : int
        Unique identifier.
    lemma : str
        Lemma
    pos : str
        Part of speech
    domain : int
        Domain
    """

    def __init__(self, plwordnet, uid, lemma, pos, domain):
        self._plwordnet = plwordnet
        self._uid = uid
        self._lemma = lemma
        self._pos = pos
        self._domain = domain

    def uid(self):
        return self._uid

    def name(self):
        return self._lemma

    def antonyms(self):
        return self._plwordnet.antonyms(self.uid())

    def pos(self):
        char = self._plwordnet._pos[self._pos].char
        if char in wordnet.POS:
            return wordnet.POS[char]

    def domain(self):
        return self._domain

    def domain_str(self):
        return self._plwordnet._domains.get(self._domain)
