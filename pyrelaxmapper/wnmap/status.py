# -*- coding: utf-8 -*-


class Mapping:
    """RL Mapping class between a source and target unit.

    """
    # class Method(Enum):
    #     """Mapping condition used."""
    #     dict = auto()
    #     counts = auto()
    #     rlabel = auto()
    #     manual = auto()

    def __init__(self, source_id, target_id, info, method=''):
        self.source_id = source_id
        self.target_id = target_id
        self.info = info
        self.method = method

    def __repr__(self):
        return '{}->{} ({})'.format(self.source_id, self.target_id, self.method)


class Status:
    """Status of Relaxation Labeling algorithm."""
    def __init__(self):
        pass
        # map_done = None
        # map_todo = None
        #
        # info_done = None
        # info_todo = None
        #
        # all_weights = None
        # all_candidates = None
        #
        # source = None
        # target = None
