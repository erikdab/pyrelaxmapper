# -*- coding: utf-8 -*-
import logging.config

from pyrelaxmapper import conf

logging.config.fileConfig(conf.last_in_paths('logging.ini'))
logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = """Erik David Burnell"""
__email__ = 'erik.d.burnell@gmail.com'
__version__ = '0.1.0'

APPLICATION = 'pyrelaxmapper'
