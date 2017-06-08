# -*- coding: utf-8 -*-
from configparser import ConfigParser


class Options:
    """Application configuration options."""
    def __init__(self, file):
        config = ConfigParser()
        config.read_file(file)

        # self.make_compilation = int(config.get('runapp', 'make_compilation'))
        # self.make_translation = int(config.get('runapp', 'make_translation'))
        # self.generate_equiv = int(config.get('runapp', 'generate_equiv'))
        # self.make_eval = int(config.get('runapp', 'make_eval'))
        # self.insert_pierwsi = int(config.get('runapp', 'insert_pierwsi'))

        self.mode = config.get('main', 'mode')
        self.constraints = config.get('main', 'constraints')
        # self.dboutfile = config.get('main', 'db_out_file')
        # self.result_eval_file = config.get('main', 'result_eval_file')
        # self.wordnet_graph_file = config.get('main', 'wordnet_graph_file')
        # self.max_path_length = int(config.get('main', 'max_path_length'))
        # self.pierwsi_last_suffix = config.get('main', 'pierwsi_last_suffix')

        self.dict_file = config.get('rlapp', 'dict_file')
        self.syns_hipe_file = config.get('rlapp', 'syns_hipe_file')
        self.syns_hipo_file = config.get('rlapp', 'syns_hipo_file')
        self.syns_text_file = config.get('rlapp', 'syns_text_file')
        self.synsets_file = config.get('rlapp', 'synsets_file')
        self.units_file = config.get('rlapp', 'units_file')
        self.pierwsi_file = config.get('rlapp', 'pierwsi_file')
        self.pozostali_file = config.get('rlapp', 'pozostali_file')
        self.reczni_file = config.get('rlapp', 'reczni_file')
        self.translated_file = config.get('rlapp', 'translated_file')

        self.dbconfig = config.get('wnloom', 'wnloom_conncet_db_cfg')
        self.dbconfig_insert = config.get('wnloom', 'wnloom_insert_db_cfg')
        self.wnloompath = config.get('wnloom', 'wnloom_path')

        self._validate()

    def _validate(self):
        pass
        # if self.generate_equiv == 1 and self.make_eval == 1:
        #    raise ValueError('When make evaluation is enabled, then set generate_only must be 0!')
