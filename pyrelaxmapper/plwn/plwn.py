# -*- coding: utf-8 -*-
import os
import logging
from collections import defaultdict

from pyrelaxmapper import wordnet, utils
from pyrelaxmapper.plwn import queries, files

logger = logging.getLogger()


# domains! from unitsstr
class PLWordNet(wordnet.WordNet):
    """plWordNet wordnet interface for the MySQL plWN database.

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
        self._hypernym_layers_uid = {}
        self._hyponym_layers_uid = {}
        self._manual = {}
        self._lemma_synsets = {}

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
            section_ = parser[section]
            self.db_file = os.path.expanduser(section_.get('db-file'))
            self.make_session()
            self.pos_file = os.path.expanduser(section_.get('pos-file', ''))
            self.domain_file = os.path.expanduser(section_.get('domain-file', ''))
            self.version = section_.get('version', None)
            if not self.version:
                self.version = queries.version(self.make_session())
            self.pos = parser.get('relaxer', 'pos', fallback='').split(',')

        def make_session(self):
            """Start a DB connection to plWordNet database.

            Returns
            -------

            """
            return utils.make_session(self.db_file)

    POS = {'v': 1, 'n': 2, 'r': 3, 'a': 4}
    _POS = {1: 'v', 2: 'n', 3: 'r', 4: 'a',
            5: 'v', 6: 'n', 7: 'r', 8: 'a'}

    # should be in DB
    # add weights
    # status = ['Nie przetworzone', 'Częściowo przetworzone', 'Przetworzone',
    #           'Błędne', 'Sprawdzone', 'Wątpliwe']

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
        return self._config.version

    def synsets(self, lemma, pos=None):
        return (synset for synset in self._synsets.values() if lemma in synset.lemma_names())

    def all_lunits(self):
        return self._lunits.values()

    def all_lemmas(self):
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

    def hypernym_layers(self, id_):
        return self._hypernym_layers_uid.get(int(id_), [])

    def hyponyms(self, id_):
        return self._hyponyms.get(int(id_), [])

    def hyponym_layers(self, id_):
        return self._hyponym_layers_uid.get(int(id_), [])

    def antonyms(self, id_):
        return self._antonyms.get(int(id_), [])

    # Some are missing because PWN only stores nouns now.
    def mappings(self, other_wn, recurse=True):
        """Existing mappings with another wordnet.

        PWordNet unitsstr parsing:
            unitsstr:
               "(butyl alcohol 1* (sbst) [sbst] | butanol 1* (sbst))"
            extract:
                "butyl alcohol 1"
            into sense tuple:
               txt, num = ('butyl_alcohol', 1)

        Parameters
        ----------
        other_wn : pyrelaxmapper.wordnet.WordNet
            Short name of target WordNet to look for existing mappings to.
        recurse : bool
            Whether to check the other wordnet, only once

        Returns
        -------
        tuple of (dict, list)
            Results: (mapped, dest_missing)
        """
        # One-to-many? Max target, avg
        target_name = other_wn.name()
        if target_name in ['PWN', 'WordNet']:
            session = self._config.make_session()
            manual = defaultdict(set)
            missing = []
            dest = set()
            for row in queries.pwn_mappings(session).all():
                *txt, num = row.unitsstr[1:row.unitsstr.find('*')].lower().split(' ')
                txt = '_'.join(txt)
                pos = self._POS[row.pos]
                p_uid = '{}.{}.{:0>2}'.format(txt, pos, num)
                d_syn = other_wn.synset(p_uid)
                if d_syn:
                    dest.add(d_syn.uid())
                    manual[row.pl_uid].add(d_syn.uid())
                else:
                    missing.append(p_uid)
            lengths = [len(targets) for targets in manual.values()]
            max_ = max(lengths)
            avg_ = sum(lengths) / len(lengths)
            count_ = len(manual)
            logger.info('max: {}, avg: {}, count: {}'.format(max_, avg_, count_))
            # max: 21, avg: 1.0757550548613362, count: 114197
            return manual, missing

        return super().mappings(other_wn, False)

    def load(self):
        """Load plWordNet data from MySQL."""

        # Create method to read this
        if not self._pos and self._config.pos_file:
            with open(self._config.pos_file) as file:
                self._pos = files.load_pos(file)

        if not self._domains and self._config.domain_file:
            with open(self._config.domain_file) as file:
                self._domains = files.load_domains(file)

        session = self._config.make_session()

        text = repr(self)

        if not self._synsets:
            pos = []
            for uid in self._config.pos:
                pos.append(self.POS[uid])

            # Lexical Units
            # TODO: Glosses
            logger.info('{} Loading lexical units.'.format(text))
            self._lunits = {lunit.id_: PLLexicalUnit(self, lunit.id_, lunit.lemma, lunit.pos,
                                                     lunit.domain)
                            for lunit in queries.lunits(session, pos)}

            # Synsets
            # TODO: definition could probably be useful, unitsstr maybe?
            logger.info('{} Loading synsets.'.format(text))
            self._synsets = {}
            for synset in queries.synsets(session, pos):
                s_lunits = {int(unitindex): self._lunits[int(lex_id)]
                            for lex_id, unitindex in
                            zip(synset.lex_ids.split(','), synset.unitindexes.split(','))}
                self._synsets[synset.id_] = PLSynset(self, synset.id_, synset.definition, s_lunits)

            # Relation Types
            self._reltypes = {reltype.name: reltype for reltype in queries.reltypes(session)}

            # Synset Relations:
            logger.info('{} Loading hyper/hypo relations.'.format(text))
            self._hypernyms = {}
            self._hyponyms = {}
            for hypernym in queries.synset_relations(session, self._reltypes['hiperonimia'].id_,
                                                     pos):
                self._hypernyms.setdefault(hypernym.child_id, []).append(
                    self.synset(hypernym.parent_id))
            for hyponym in queries.synset_relations(session, self._reltypes['hiponimia'].id_, pos):
                self._hyponyms.setdefault(hyponym.child_id, []).append(
                    self.synset(hyponym.parent_id))

            logger.info('{} Calculating hipernym paths.'.format(text))
            self._hypernym_paths = {synset.uid(): synset.find_hypernym_paths(synset)
                                    for synset in self._synsets.values()}

            logger.info('{} Calculating hyper/hypo layers.'.format(text))
            self._hypernym_layers_uid, self._hyponym_layers_uid = self.find_hh_layers()

            # Lexical Relations:
            # logger.info('{} Loading antonymy relations.'.format(text))
            # antonym_relid = self._reltypes['antonimia'].id_
            # for antonym in queries.lexical_relations(session, antonym_relid, pos):
            #     self._antonyms.setdefault(antonym.child_id, []).append(
            #         self._lunits[antonym.parent_id])

        self._loaded = True
        return self
        # lemmas to synsets should be part of it!


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

    def hypernym_layers(self):
        if self._hyper is None:
            self._hyper = self._plwordnet.hypernym_layers(self._uid)
        return self._hyper

    def hyponyms(self):
        return self._plwordnet.hyponyms(self._uid)

    def hyponym_layers(self):
        if self._hypo is None:
            self._hypo = self._plwordnet.hyponym_layers(self._uid)
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
