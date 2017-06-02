# -*- coding: utf-8 -*-
"""General Utilities."""
import re


def multi_replace(text, replacements, ignore_case=False):
    """
    Given a string and a dict, replaces occurrences of the dict keys found in the
    string, with their corresponding values. The replacements will occur in "one pass",
    i.e. there should be no clashes.

    Parameters
    ----------
    text : str
        string to perform replacements on
    replacements : dict
        replacement dictionary {str_to_find: str_to_replace_with}
    ignore_case : bool
        whether to ignore case when looking for matches

    Returns
    -------
    str
        str the replaced string
    """
    # Sort by length so that the shorter strings don't replace the longer ones.
    rep_sorted = sorted(replacements, key=lambda s: len(s[0]), reverse=True)

    rep_escaped = [re.escape(replacement) for replacement in rep_sorted]

    pattern = re.compile("|".join(rep_escaped), re.I if ignore_case else 0)

    return pattern.sub(lambda match: replacements[match.group(0)], text)
