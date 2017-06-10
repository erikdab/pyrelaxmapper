# -*- coding: utf-8 -*-
import random
import time
import logging
import numpy as np

from nltk.corpus import wordnet as pwn

logger = logging.getLogger()


class Stats:
    """Statistics of Relaxation Labeling algorithm."""

    toc = time.clock()
    tic = time.clock()

    line_nr = 0
    which_one = 0
    suggestions = 0  # algorithm suggestions
    selected = 0  # algorithm suggestions accepted by the user
    mapped_count = 0  # algorithm selected without user interaction

    def __init__(self, config, status):
        self._config = config
        self.to_eval = self._select_eval(status.map_todo)

    def __str__(self):
        logger.info("time: {}".format(self.toc - self.tic))
        logger.info("Suggestions: {}".format(self.suggestions))
        logger.info("Accepted by user: {}".format(self.selected))
        logger.info("Selected by algorithm: {}".format(self.mapped_count))

    # TODO: Allow selecting which ones to evaluate
    def _select_eval(self, rest):
        """Select random elements for manual evaluation."""
        syn_ids = list(rest.keys())
        selected = set()
        while len(selected) < 5000:
            idx = random.randrange(len(rest))
            selected.add(syn_ids[idx])
        logger.info('Selected {} synsets to test manually\n'.format(len(selected)))
        return selected

    def _eval_prompt(self, suggestions, weights, syns_text, hiper_pl, hipo_pl, current_syn,
                     candidates, step2, line_nr, which_one, selected):
        """Manual evaluation prompt."""
        suggestions = suggestions + 1
        try:
            maxind = np.nonzero([m == max(weights) for m in weights])[0]
        except IndexError:
            logger.debug('Can not find candidates..')
            maxind = 0

        # Some synsets are empty...
        try:
            hipern_pl = [syns_text[s] for s in hiper_pl]
        except KeyError:
            logger.debug('Synset empty.')
            hipern_pl = []
        logger.info('Polish hipernyms: {}'.format(hipern_pl[0:5]))

        try:
            hipon_pl = [syns_text[s] for s in hipo_pl]
        except KeyError:
            logger.debug('Synset empty.')
            hipon_pl = []
        logger.info('Polish hiponyms: {}'.format(hipon_pl[0:5]))

        logger.info('Candidates count: {}'.format(len(weights)))
        logger.info('Candidates for {}:'.format(current_syn))
        for idx in range(len(weights)):
            # przegladamy potencjalne dopasowania - elementy tablicy kandydaci
            logger.info("\n", idx + 1, " ", candidates[idx], ": ",
                        pwn.synset(str(candidates[idx])).lemma_names())
            logger.info("\nhipernyms: ", [i.name() for i in
                                          pwn.synset(candidates[idx]).hypernym_paths()[0]][
                                         0:5])
            logger.info("\nhiponyms: ",
                        [i.name() for i in pwn.synset(candidates[idx]).hyponyms()][0:5], "\n")

        logger.info("\nAlgorithm selected:")
        if type(maxind) != list:
            maxind = [maxind]
        for n in range(len(maxind[0])):
            logger.info(maxind, maxind[0], maxind[0][n] + 1, " ",
                        candidates[int(maxind[0][n])])
        try:
            odp = input("\nSelect a candidate to assign (0-resign):")
            if odp != '0':
                line_nr = line_nr + 1
                which_one = which_one + 1
                step2.write(str(line_nr) + " " + str(current_syn) + " " + str(
                    candidates[int(odp) - 1]) + "\n")
                logger.info("\nans: ", odp, " Assigned ", candidates[int(odp) - 1], " do ",
                            current_syn,
                            ".\n")
                if int(odp) - 1 in maxind[0]:
                    selected = selected + 1
            odp = input("\nEnter any Key to continue")
        except ValueError:
            logger.info("Wrong value???")
        if which_one % 5 == 1:
            logger.info("Suggestions: ", suggestions)
            logger.info("Accepted by user: ", selected)
            odp = input("\nEnter any Key to continue")

    def _toeval(self):
        pass
        # if mode == 'i' and current_syn in to_eval:
        #     _eval_prompt(suggestions, weights, syns_text, hiper_pl, hipo_pl, current_syn,
        #                  candidates, step2, line_nr, which_one, selected)
