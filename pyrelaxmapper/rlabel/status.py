# -*- coding: utf-8 -*-
# from enum import Enum


class Mapping:
    # How was the mapping formed.
    # class Method(Enum):
    #     dict = 1 presence = 2 rlabel = 3

    def __init__(self, source_id, target_id, info, method='rlabel'):
        self.source_id = None
        self.target_id = None
        self.info = None


class Status:
    """Status of Relaxation Labeling algorithm."""
    map_done = None
    map_todo = None

    info_done = None
    info_todo = None

    all_weights = None
    all_candidates = None

    source = None
    target = None

    def __init__(self):
        pass
